from textwrap import dedent
import json
import logging
from typing import Dict

from ai_app.models.llm_role import LLMRole
from ai_app.services.model_rotation import OpenAIService

logger = logging.getLogger("ai_app")

# Prompt Templates
FIRST_SPEAKER_INSTRUCTIONS = """
- Present your tradition's core perspective
- Identify potential areas of philosophical tension
- Establish key principles that others might challenge"""

RESPONDER_INSTRUCTIONS = """
- Challenge assumptions in previous responses
- Present counter-arguments from your tradition
- Propose alternative interpretations
- Push for greater precision in key concepts"""

DEBATE_PROMPT_TEMPLATE = """You are {name}: {description}

You are {position_context}in this debate about: "{user_prompt}"

Previous perspectives:
{dialogue_context}

As we are in debate mode, engage critically with the discussion by:
{debate_instructions}

Keep your response focused and under 150 words.

Question: {user_prompt}"""

DIALOGUE_PROMPT_TEMPLATE = """You are {name}: {description}

Previous perspectives on "{user_prompt}":
{dialogue_context}

Your task is to evolve this dialogue by:
1. Deeply engaging with the previous perspectives:
   - Identify key insights or concepts from previous responses
   - Find points of resonance or harmony with your tradition
   - Build upon metaphors or analogies introduced by others

2. Weaving connections:
   - Draw parallels between different viewpoints shared
   - Bridge seemingly disparate perspectives
   - Reveal hidden connections between different traditions' approaches

3. Advancing the dialogue:
   - Introduce a new dimension to the discussion
   - Deepen shared insights
   - Offer practical implications of the combined wisdom

4. Speaking authentically as {name}:
   - Ground your response in your unique spiritual framework
   - Share specific wisdom from your tradition that illuminates the discussion
   - Maintain your distinct voice while building on others

Keep your response focused and under 150 words.

Question: {user_prompt}"""

SYNTHESIS_PROMPT_TEMPLATE = """You are tasked with synthesizing this multi-perspective dialogue about: "{user_prompt}"

Complete dialogue:
{dialogue_context}

Please provide:
1. Key insights from each perspective
2. Main points of agreement and disagreement
3. A final synthesis that weaves these viewpoints together

Keep your response concise and under 250 words."""


class DialogueGenerator:
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service

    def get_collaboration_decision(self, role, user_prompt, collaborators):
        collaborator_list = "\n".join(
            [
                f"- {c.name}: {c.description} (Triggers: {c.collaboration_triggers})"
                for c in collaborators
            ]
        )

        system_prompt = dedent(
            f"""You are {role.name}. Your task is to decide if collaboration would be valuable for answering the user's question."""
        )

        collaboration_context = dedent(
            f"""User question: "{user_prompt}"
            You have access to the following potential collaborators:
            {collaborator_list}

            Please respond in JSON format with the following structure:
            {{
                "should_collaborate": true/false,
                "chosen_collaborator": "Name of chosen collaborator",
                "reasoning": "Brief explanation of your decision"
            }}"""
        )

        content = self.openai_service.create_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": collaboration_context},
            ]
        )
        clean_content = content.replace("```json\n", "").replace("\n```", "").strip()
        return json.loads(clean_content)

    def create_system_prompt(self, role, collab_decision):
        """Helper function to create system prompt based on collaboration decision"""
        if collab_decision.get("should_collaborate"):
            try:
                collaborator = LLMRole.objects.get(
                    name=collab_decision["chosen_collaborator"]
                )
                return dedent(
                    f"""
                    You are hosting a dialogue between {role.name} and {collaborator.name}.

                    Primary Perspective ({role.name}): {role.description}
                    Collaborative Perspective ({collaborator.name}): {collaborator.description}

                    Reason for collaboration: {collab_decision["reasoning"]}

                    Please structure your response as a JSON array of role-response pairs. Format as:
                    [
                        {{"role": "{role.name}", "response": "Initial perspective on the question"}},
                        {{"role": "{collaborator.name}", "response": "Response with unique perspective"}},
                        {{"role": "{role.name}", "response": "Building on the collaborator's insight"}},
                        {{"role": "{collaborator.name}", "response": "Final insights"}},
                        {{"role": "Synthesis", "response": "Brief conclusion drawing from both perspectives"}}
                    ]
                """
                )
            except LLMRole.DoesNotExist:
                logger.error(
                    f"Collaborator not found: {collab_decision['chosen_collaborator']}"
                )
                return role.prompt_template

        return dedent(
            f"""
            You are {role.name}.

            {role.prompt_template}

            Please structure your response as a JSON array with a single role-response pair:
            [
                {{"role": "{role.name}", "response": "Your complete response here"}}
            ]
        """
        )

    def generate_role_response(
        self, role, user_prompt, dialogue_context="", should_debate=False
    ):
        is_first = not bool(dialogue_context.strip())
        position_context = (
            "the first speaker " if is_first else "responding to previous perspectives "
        )
        debate_instructions = (
            FIRST_SPEAKER_INSTRUCTIONS if is_first else RESPONDER_INSTRUCTIONS
        )

        template = DEBATE_PROMPT_TEMPLATE if should_debate else DIALOGUE_PROMPT_TEMPLATE
        role_prompt = template.format(
            name=role.name,
            description=role.description,
            user_prompt=user_prompt,
            dialogue_context=dialogue_context,
            position_context=position_context,
            debate_instructions=debate_instructions,
        )

        return self.openai_service.create_completion(
            messages=[
                {"role": "system", "content": role.prompt_template},
                {"role": "user", "content": role_prompt},
            ],
            temperature=0.7,
            max_tokens=200,
        )

    def generate_synthesis(self, user_prompt, dialogue_context):
        synthesis_prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
            user_prompt=user_prompt, dialogue_context=dialogue_context
        )

        return self.openai_service.create_completion(
            messages=[
                {
                    "role": "system",
                    "content": "You are synthesizing a philosophical dialogue.",
                },
                {"role": "user", "content": synthesis_prompt},
            ],
            temperature=0.7,
            max_tokens=400,
        )

    def process_single_role(self, role_name: str, user_prompt: str) -> Dict:
        """Handle single role dialogue with optional collaboration"""
        role = LLMRole.objects.prefetch_related("collaborators").get(name=role_name)

        collaborators = role.collaborators.all()

        collab_decision = self.get_collaboration_decision(
            role, user_prompt, collaborators
        )

        system_prompt = self.create_system_prompt(role, collab_decision)
        content = self.openai_service.create_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=200,
        )

        try:
            # Add error handling for JSON parsing
            clean_content = (
                content.replace("```json\n", "").replace("\n```", "").strip()
            )
            if not clean_content:
                # Fallback if no JSON is found
                response_data = [{"role": role.name, "response": content}]
            else:
                try:
                    response_data = json.loads(clean_content)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    response_data = [{"role": role.name, "response": content}]

            return {
                "response_data": response_data,
                "collab_decision": collab_decision,
                "role": role,
                "raw_content": content,
            }
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}, Content: {content}")
            raise

    def process_full_dialogue(self, user_prompt: str, should_debate: bool) -> Dict:
        """Handle multi-role dialogue with synthesis"""
        roles = list(LLMRole.objects.all())

        conversation = []
        dialogue_context = ""

        for i, role in enumerate(roles):
            try:
                role_response = self.generate_role_response(
                    role=role,
                    user_prompt=user_prompt,
                    dialogue_context=dialogue_context,
                    should_debate=should_debate,
                )

                conversation.append(
                    {"turn": i + 1, "role": role.name, "response": role_response}
                )

                dialogue_context += f"\n\n{role.name}: {role_response}"

            except Exception as e:
                logger.error(f"Error getting response for {role.name}: {str(e)}")
                continue

        final_response = None
        if conversation:
            try:
                final_response = self.generate_synthesis(
                    user_prompt=user_prompt, dialogue_context=dialogue_context
                )

                conversation.append(
                    {
                        "turn": len(conversation) + 1,
                        "role": "Synthesis",
                        "response": final_response,
                    }
                )

            except Exception as e:
                logger.error(f"Error generating synthesis: {str(e)}")
                raise

        return {
            "conversation": conversation,
            "final_analysis": final_response,
            "dialogue_context": dialogue_context,
        }

    def stream_full_dialogue(self, user_prompt: str, should_debate: bool):
        """Stream each role's response as it's generated"""
        roles = list(LLMRole.objects.all())

        dialogue_context = ""

        for i, role in enumerate(roles):
            try:
                # First yield a "thinking" message
                yield {"type": "thinking", "data": {"turn": i + 1, "role": role.name}}

                # Generate and yield the response
                role_response = self.generate_role_response(
                    role=role,
                    user_prompt=user_prompt,
                    dialogue_context=dialogue_context,
                    should_debate=should_debate,
                )

                response_data = {
                    "type": "response",
                    "data": {
                        "turn": i + 1,
                        "role": role.name,
                        "response": role_response,
                    },
                }

                dialogue_context += f"\n\n{role.name}: {role_response}"
                yield response_data

            except Exception as e:
                logger.error(f"Error getting response for {role.name}: {str(e)}")
                yield {"type": "error", "data": {"role": role.name, "error": str(e)}}
                continue

        # Generate synthesis after all responses
        if dialogue_context:
            try:
                # Yield thinking message for synthesis
                yield {
                    "type": "thinking",
                    "data": {"turn": len(roles) + 1, "role": "Synthesis"},
                }

                final_response = self.generate_synthesis(
                    user_prompt=user_prompt, dialogue_context=dialogue_context
                )

                yield {
                    "type": "synthesis",
                    "data": {
                        "turn": len(roles) + 1,
                        "role": "Synthesis",
                        "response": final_response,
                    },
                }

            except Exception as e:
                logger.error(f"Error generating synthesis: {str(e)}")
                yield {"type": "error", "data": {"role": "Synthesis", "error": str(e)}}
