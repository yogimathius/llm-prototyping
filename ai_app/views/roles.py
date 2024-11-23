from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ai_app.models.llm_role import LLMRole
from ai_app.services.response_formatter import ResponseFormatter


@csrf_exempt
def list_roles(request):
    roles = LLMRole.objects.all()
    roles_data = ResponseFormatter.format_roles(roles)
    return JsonResponse({"roles": roles_data}, safe=False)
