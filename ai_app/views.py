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
    # Parse request data
    try:
        logger.info(f"Received request body: {request.body}")
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
            model="gpt-4o",
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
        model="gpt-4o",
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
