from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ai_app.models.history import History
from ai_app.models.llm_role import LLMRole
from ai_app.models.user import User
from ai_app.services.dialogue_generator import DialogueGenerator
from ai_app.services.model_rotation import OpenAIService
import json
import logging

logger = logging.getLogger("ai_app")


@csrf_exempt
@require_POST
def ask_role(request):
    try:
        data = json.loads(request.body)
        user_prompt = data.get("prompt")
        role_name = data.get("role")

        if not user_prompt or not role_name:
            return JsonResponse({"error": "Missing prompt or role"}, status=400)

        openai_service = OpenAIService()
        dialogue_generator = DialogueGenerator(openai_service)
        result = dialogue_generator.process_single_role(role_name, user_prompt)

        History.objects.create(
            user=User.objects.get(username="testuser"),
            role=result["role"],
            prompt=user_prompt,
            response=result["raw_content"],
        )

        return JsonResponse(
            {
                "response": result["response_data"],
                "collaboration": (
                    result["collab_decision"]
                    if result["collab_decision"].get("should_collaborate")
                    else None
                ),
            }
        )

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except LLMRole.DoesNotExist:
        return JsonResponse({"error": f"Role '{role_name}' not found"}, status=404)
    except Exception as e:
        logger.error(f"Error in request processing: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@csrf_exempt
@require_POST
def full_dialogue(request):
    try:
        data = json.loads(request.body)
        user_prompt = data.get("prompt")
        logger.info(f"Received prompt: {user_prompt}")

        if not user_prompt:
            return JsonResponse({"error": "No prompt provided"}, status=400)

        openai_service = OpenAIService()
        dialogue_generator = DialogueGenerator(openai_service)
        result = dialogue_generator.process_full_dialogue(user_prompt)

        return JsonResponse(
            {
                "original_prompt": user_prompt,
                "conversation": result["conversation"],
                "final_analysis": result["final_analysis"],
            }
        )

    except json.JSONDecodeError:
        logger.error("JSON decode error", exc_info=True)
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error in full_dialogue: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)
