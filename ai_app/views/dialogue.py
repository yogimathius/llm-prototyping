from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ..models import History, LLMRole, User
from ..services.dialogue_generator import DialogueGenerator
from ..services.model_rotation import OpenAIService
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

        role = LLMRole.objects.prefetch_related("collaborators").get(name=role_name)
        collaborators = role.collaborators.all()

        openai_service = OpenAIService()
        dialogue_generator = DialogueGenerator(openai_service)

        collab_decision = dialogue_generator.get_collaboration_decision(
            role, user_prompt, collaborators
        )
        system_prompt = dialogue_generator.create_system_prompt(role, collab_decision)

        content = openai_service.create_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

        clean_content = content.replace("```json\n", "").replace("\n```", "").strip()
        response_data = json.loads(clean_content)

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

        roles = list(LLMRole.objects.all())
        logger.info(f"Retrieved roles: {[role.name for role in roles]}")

        openai_service = OpenAIService()
        dialogue_generator = DialogueGenerator(openai_service)

        conversation = []
        dialogue_context = ""

        # Process each role sequentially
        for i, role in enumerate(roles):
            logger.info(f"Processing role {i + 1}: {role.name}")

            try:
                logger.info(
                    f"Making API call for {role.name} with context length: {len(dialogue_context)}"
                )
                role_response = dialogue_generator.generate_role_response(
                    role=role,
                    user_prompt=user_prompt,
                    dialogue_context=dialogue_context,
                )

                logger.info(f"Response from {role.name}: {role_response}")

                conversation.append(
                    {"turn": i + 1, "role": role.name, "response": role_response}
                )

                dialogue_context += f"\n\n{role.name}: {role_response}"

            except Exception as e:
                logger.error(f"Error getting response for {role.name}: {str(e)}")
                continue

        # Generate final synthesis
        if conversation:
            try:
                logger.info("Generating final synthesis")
                final_response = dialogue_generator.generate_synthesis(
                    user_prompt=user_prompt, dialogue_context=dialogue_context
                )

                logger.info(f"Final synthesis: {final_response}")

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
