import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import os
from ai_app.ai_handler import AIHandler
from ai_app.models import LLMRole
from openai import OpenAI

# Configure logger properly
logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def ask_role(request):
    logger.info("Received ask_role request")
    try:
        data = json.loads(request.body)
        user_prompt = data.get("prompt")
        role_name = data.get("role")

        if not user_prompt:
            logger.warning("No prompt provided in request")
            return JsonResponse({"error": "No prompt provided"}, status=400)

        # Get the requested role
        try:
            role = LLMRole.objects.get(name=role_name)
        except LLMRole.DoesNotExist:
            logger.error(f"Role not found: {role_name}")
            return JsonResponse({"error": f"Role '{role_name}' not found"}, status=404)

        try:
            ai_handler = AIHandler()

            # Add role's prompt template to the user prompt
            enhanced_prompt = f"""
            Role: {role.name}
            Role Description: {role.prompt_template}
            Question: {user_prompt}
            """

            response = ai_handler.get_role_response(role, enhanced_prompt)

            if response:
                logger.info("Successfully generated response")
                logger.debug(f"Response length: {len(response)}")
                return JsonResponse(
                    {
                        "role": role.name,
                        "response": response,
                        "original_prompt": user_prompt,
                    }
                )
            else:
                logger.error("Empty response from AI Handler")
                return JsonResponse(
                    {"error": "Failed to generate response"}, status=500
                )

        except Exception as e:
            logger.error(f"Error getting response from LLM: {str(e)}", exc_info=True)
            return JsonResponse({"error": "Failed to generate response"}, status=500)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body", exc_info=True)
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in ask_role view: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)
