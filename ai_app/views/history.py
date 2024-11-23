from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import History
from ..services.response_formatter import ResponseFormatter
import logging

logger = logging.getLogger("ai_app")


@csrf_exempt
def get_conversation_history(request):
    history = History.objects.all().order_by("-created_at")
    history_data = ResponseFormatter.format_history(history)
    return JsonResponse({"history": history_data})
