from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import os
from ai_app.models import History, LLMRole, User
from openai import OpenAI
import logging
from django.forms.models import model_to_dict
from textwrap import dedent
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Replace any direct token references with
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# or
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger("ai_app")

# Initialize OpenAI client
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=GITHUB_TOKEN,
)

model_name = "gpt-4o-mini"


@csrf_exempt
def get_all_roles(request):
    roles = LLMRole.objects.all()
    roles_data = [
        {
            "name": role.name,
            "description": role.description,
        }
        for role in roles
    ]
    return JsonResponse({"roles": roles_data}, safe=False)


@csrf_exempt
@require_POST
def ask_role(request):
    # Parse request data
    try:
        logger.info("Starting API request...")
        data = json.loads(request.body)
        user_prompt = data.get("prompt")
        role_name = data.get("role")

        if not user_prompt or not role_name:
            return JsonResponse({"error": "Missing prompt or role"}, status=400)

        # Get role and collaborators
        role = LLMRole.objects.prefetch_related("collaborators").get(name=role_name)
        collaborators = role.collaborators.all()

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}, Request body: {request.body}")
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except LLMRole.DoesNotExist:
        return JsonResponse({"error": f"Role '{role_name}' not found"}, status=404)
    except Exception as e:
        logger.error(f"Error in request processing: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)

    # Get collaboration decision
    try:
        collab_decision = get_collaboration_decision(role, user_prompt, collaborators)
        system_prompt = create_system_prompt(role, collab_decision)
    except Exception as e:
        logger.error(f"Error in collaboration processing: {str(e)}")
        return JsonResponse({"error": "Error processing collaboration"}, status=500)

    # Generate final response
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content
        clean_content = content.replace("```json\n", "").replace("\n```", "").strip()
        response_data = json.loads(clean_content)

        # Store conversation
        History.objects.create(
            user=User.objects.get(username="testuser"),
            role=role,
            prompt=user_prompt,
            response=content,
        )

        return JsonResponse(
            {
                "response": response_data,
                "collaboration": (
                    collab_decision
                    if collab_decision.get("should_collaborate")
                    else None
                ),
            }
        )

    except Exception as e:
        logger.error(f"Error in response generation: {str(e)}")
        return JsonResponse({"error": "Error generating response"}, status=500)


def get_collaboration_decision(role, user_prompt, collaborators):
    """Helper function to get collaboration decision from LLM"""
    collaborator_list = "\n".join(
        [
            f"- {c.name}: {c.description} (Triggers: {c.collaboration_triggers})"
            for c in collaborators
        ]
    )

    collaboration_context = dedent(
        f"""
        You are {role.name}. 

        User question: "{user_prompt}"

        You have access to the following potential collaborators:

        {collaborator_list}

        Based on the user's question and the available collaborators' expertise and triggers, 
        should you collaborate with any of them to provide a better answer? If yes, which one?

        Please respond in JSON format:
        {{
            "should_collaborate": true/false,
            "chosen_collaborator": "name of collaborator or null",
            "reasoning": "brief explanation of your decision"
        }}
    """
    )

    collab_response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": collaboration_context}],
        temperature=0.7,
    )

    content = collab_response.choices[0].message.content
    clean_content = content.replace("```json\n", "").replace("\n```", "").strip()
    return json.loads(clean_content)


def create_system_prompt(role, collab_decision):
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


@csrf_exempt
def get_history(request):
    history = History.objects.all().order_by("-created_at")
    logger.info(f"History: {history}")
    history_data = [
        model_to_dict(item, fields=["id", "prompt", "response"]) for item in history
    ]

    logger.info(f"History data: {history_data}")

    for i, item in enumerate(history):
        history_data[i]["role"] = item.role.name if item.role else None
        history_data[i]["created_at"] = item.created_at.isoformat()

    return JsonResponse({"history": history_data})


def get_response(prompt, message_history):
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=message_history,
            temperature=1.0,
            top_p=1.0,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error occurred while getting response: {e}")
        return None


@csrf_exempt
@require_POST
def full_dialogue(request):
    try:
        data = json.loads(request.body)
        user_prompt = data.get("prompt")
        logger.info(f"Received prompt: {user_prompt}")

        if not user_prompt:
            return JsonResponse({"error": "No prompt provided"}, status=400)

        roles = list(LLMRole.objects.all())
        logger.info(f"Retrieved roles: {[role.name for role in roles]}")
        conversation = []
        dialogue_context = ""

        # Process each role sequentially
        for i, role in enumerate(roles):
            logger.info(f"Processing role {i + 1}: {role.name}")

            # Create role-specific prompt with accumulated context
            role_prompt = f"""You are {role.name}: {role.description}

Previous perspectives on "{user_prompt}":
{dialogue_context}

Your task is to:
1. Acknowledge and directly reference at least one previous perspective, if any
2. If you're the first to respond, simply state your own perspective
3. If your perspective is different from the previous ones, clearly state the discrepancy
4. Either build upon, contrast with, or synthesize the ideas presented
5. Add your unique viewpoint as {role.name}
4. Keep your response focused and under 150 words

For example, if you're the Alchemist and previous speakers discussed consciousness:
"Building on the Quantum Philosopher's observation about consciousness as an observer, 
I see this through the lens of transformation..."

Question: {user_prompt}

Please provide your perspective while explicitly engaging with the previous responses."""

            try:
                logger.info(
                    f"Making API call for {role.name} with context length: {len(dialogue_context)}"
                )
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": role.prompt_template},
                        {"role": "user", "content": role_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=200,
                )

                role_response = response.choices[0].message.content
                logger.info(f"Response from {role.name}: {role_response}")

                # Add to conversation and update context
                conversation.append(
                    {"turn": i + 1, "role": role.name, "response": role_response}
                )

                dialogue_context += f"\n\n{role.name}: {role_response}"

            except Exception as e:
                logger.error(f"Error getting response for {role.name}: {str(e)}")
                continue

        # Generate final synthesis
        if conversation:
            synthesis_prompt = f"""You are tasked with synthesizing this multi-perspective dialogue about: "{user_prompt}"

Complete dialogue:
{dialogue_context}

Please provide:
1. Key insights from each perspective
2. Main points of agreement and disagreement
3. A final synthesis that weaves these viewpoints together

Keep your response concise and under 250 words."""

            try:
                logger.info("Generating final synthesis")
                synthesis = client.chat.completions.create(
                    model=model_name,
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

                final_response = synthesis.choices[0].message.content
                logger.info(f"Final synthesis: {final_response}")

                # Add synthesis to conversation
                conversation.append(
                    {
                        "turn": len(conversation) + 1,
                        "role": "Synthesis",
                        "response": final_response,
                    }
                )

            except Exception as e:
                logger.error(f"Error generating synthesis: {str(e)}")
                return JsonResponse(
                    {"error": "Failed to generate synthesis"}, status=500
                )

        return JsonResponse(
            {
                "original_prompt": user_prompt,
                "conversation": conversation,
                "final_analysis": final_response if conversation else None,
            }
        )

    except json.JSONDecodeError:
        logger.error("JSON decode error", exc_info=True)
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error in full_dialogue: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)
