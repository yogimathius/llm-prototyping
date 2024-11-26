from django.http import JsonResponse, StreamingHttpResponse
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

        if not request.body:
            logger.error("Empty request body received")
            return JsonResponse({"error": "Empty request body"}, status=400)

        data = json.loads(request.body)
        user_prompt = data.get("prompt")
        role_name = data.get("role")

        if not user_prompt or not role_name:
            logger.error(
                f"Missing required fields - prompt: {user_prompt}, role: {role_name}"
            )
            return JsonResponse({"error": "Missing prompt or role"}, status=400)

        openai_service = OpenAIService()
        dialogue_generator = DialogueGenerator(openai_service)

        result = dialogue_generator.process_single_role(role_name, user_prompt)

        History.objects.create(
            user=User.objects.get(username="testuser"),
            prompt=user_prompt,
            response=result["raw_content"],
            role=LLMRole.objects.get(name=role_name),
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
        logger.error(f"JSON decode error: {str(e)}, Request body: {request.body}")
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
        should_debate = data.get("debate")
        logger.info(f"Received debate: {should_debate}")
        if not user_prompt:
            return JsonResponse({"error": "No prompt provided"}, status=400)

        openai_service = OpenAIService()
        dialogue_generator = DialogueGenerator(openai_service)
        result = dialogue_generator.process_full_dialogue(user_prompt, should_debate)

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


@csrf_exempt
@require_POST
def stream_dialogue(request):
    try:
        data = json.loads(request.body)
        user_prompt = data.get("prompt")
        should_debate = data.get("debate")
        if not user_prompt:
            return JsonResponse({"error": "No prompt provided"}, status=400)

        def response_stream():
            openai_service = OpenAIService()
            dialogue_generator = DialogueGenerator(openai_service)

            # Send initial message
            yield json.dumps({"type": "start", "data": {"prompt": user_prompt}}) + "\n"

            # Stream each response
            for response in dialogue_generator.stream_full_dialogue(
                user_prompt, should_debate
            ):
                yield json.dumps(response) + "\n"

            # Send completion message
            yield json.dumps({"type": "complete", "data": None}) + "\n"

        return StreamingHttpResponse(
            response_stream(), content_type="application/x-ndjson"
        )

    except json.JSONDecodeError:
        logger.error("JSON decode error", exc_info=True)
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error in stream_dialogue: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)
