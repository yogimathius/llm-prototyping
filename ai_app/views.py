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

logger = logging.getLogger("ai_app")

# Initialize OpenAI client
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"],
)


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
    try:
        # Debug the incoming request
        logger.info(f"Received request body: {request.body}")

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}, Request body: {request.body}")
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        user_prompt = data.get("prompt")
        role_name = data.get("role")

        if not user_prompt or not role_name:
            return JsonResponse({"error": "Missing prompt or role"}, status=400)

        # Get the primary role with its collaborators
        role = LLMRole.objects.prefetch_related("collaborators").get(name=role_name)
        collaborators = role.collaborators.all()

        # Create collaboration decision prompt
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

        # Ask LLM about collaboration
        try:
            collab_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": collaboration_context}],
                temperature=0.7,
            )
            logger.info(f"Collaboration response: {collab_response}")

            # Clean the response content by removing markdown formatting
            content = collab_response.choices[0].message.content
            clean_content = (
                content.replace("```json\n", "").replace("\n```", "").strip()
            )

            collab_decision = json.loads(clean_content)
            logger.info(f"Collaboration decision: {collab_decision}")

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return JsonResponse(
                {"error": "Error processing collaboration decision"}, status=500
            )

        # Proceed based on LLM's decision
        if collab_decision.get("should_collaborate"):
            try:
                collaborator = LLMRole.objects.get(
                    name=collab_decision["chosen_collaborator"]
                )

                system_prompt = f"""You are {role.name} collaborating with {collaborator.name}.
                
Primary perspective: {role.description}
Collaborative perspective: {collaborator.description}

Reason for collaboration: {collab_decision["reasoning"]}

Please provide a response that incorporates insights from both perspectives."""

                logger.info(
                    f"Collaborating with {collaborator.name}: {collab_decision['reasoning']}"
                )
            except LLMRole.DoesNotExist:
                logger.error(
                    f"Collaborator not found: {collab_decision['chosen_collaborator']}"
                )
                system_prompt = role.prompt_template
        else:
            system_prompt = role.prompt_template
            logger.info("No collaboration needed")

        # Generate final response
        try:
            response = client.chat.completions.create(
                model="gpt-4o",  # Changed from gpt-4
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
            )

            return JsonResponse(
                {
                    "response": response.choices[0].message.content,
                    "collaboration": (
                        collab_decision
                        if collab_decision.get("should_collaborate")
                        else None
                    ),
                }
            )

        except Exception as e:
            logger.error(f"OpenAI API error in final response: {str(e)}")
            return JsonResponse({"error": "Error generating response"}, status=500)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def get_history(request):
    history = History.objects.all().order_by("-created_at")

    history_data = [
        model_to_dict(item, fields=["id", "prompt", "response"]) for item in history
    ]

    for i, item in enumerate(history):
        history_data[i]["role"] = item.role.name if item.role else None
        history_data[i]["created_at"] = item.created_at.isoformat()

    return JsonResponse({"history": history_data})
