from django.forms.models import model_to_dict
import logging

logger = logging.getLogger("ai_app")


class ResponseFormatter:
    @staticmethod
    def format_roles(roles):
        return [{"name": role.name, "description": role.description} for role in roles]

    @staticmethod
    def format_history(history_items):
        history_data = [
            model_to_dict(item, fields=["id", "prompt", "response"])
            for item in history_items
        ]

        for i, item in enumerate(history_items):
            history_data[i]["role"] = item.role.name if item.role else None
            history_data[i]["created_at"] = item.created_at.isoformat()

        return history_data
