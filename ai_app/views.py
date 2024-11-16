from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import os
from ai_app.models import History, LLMRole, User
from openai import OpenAI
import logging

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
    """Handle single role-based question-answer"""
    logger.info("Received ask_role request")

    try:
        data = json.loads(request.body)
        user_prompt = data.get("prompt")
        role_name = data.get("role")

        if not user_prompt or not role_name:
            return JsonResponse({"error": "Missing prompt or role"}, status=400)

        # Get the requested role
        try:
            role = LLMRole.objects.get(name=role_name)
        except LLMRole.DoesNotExist:
            return JsonResponse({"error": f"Role '{role_name}' not found"}, status=404)

        # Create the prompt with role context
        messages = [
            {"role": "system", "content": role.prompt_template},
            {"role": "user", "content": user_prompt},
        ]

        # Get response from OpenAI
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )

            ai_response = response.choices[0].message.content
            logger.info("Successfully generated response")
            logger.debug(f"Response length: {len(ai_response)}")

            # Save to history
            History.objects.create(
                user=(
                    request.user
                    if request.user.is_authenticated
                    else User.objects.get(username="testuser")
                ),
                role=role,
                prompt=user_prompt,
                response=ai_response,
            )

            return JsonResponse(
                {
                    "role": role.name,
                    "response": ai_response,
                    "original_prompt": user_prompt,
                }
            )

        except Exception as e:
            logger.error(f"Error getting response from LLM: {str(e)}")
            return JsonResponse({"error": "Failed to generate response"}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def get_history(request):
    history = History.objects.all()
    return JsonResponse({"history": list(history)}, safe=False)
