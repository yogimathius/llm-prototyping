from django.core.management.base import BaseCommand
from ai_app.models import LLMRole

class Command(BaseCommand):
    help = 'Initialize LLM Roles'

    def handle(self, *args, **kwargs):
        roles = [
            {
                "name": "Data Analyst",
                "description": "Analyzes user input to extract key information.",
                "prompt_template": """
                You are a Data Analyst.

                Analyze the following user input to identify key focus areas and potential challenges.

                User Input: "{user_input}"

                Provide a brief analysis.
                """
            },
            {
                "name": "Strategist",
                "description": "Provides strategic insights based on user input.",
                "prompt_template": """
                You are a Strategist.

                Analyze the following user input to identify key focus areas and potential challenges.

                User Input: "{user_input}"

                Provide a brief analysis.
                """
            },
            {
                "name": "Communicator",
                "description": "Provides strategic insights based on user input.",
                "prompt_template": """
                You are a Communicator.

                Analyze the following user input to identify key focus areas and potential challenges.

                User Input: "{user_input}"

                Provide a brief analysis.
                """
            }
        ]

        for role_data in roles:
            role, created = LLMRole.objects.get_or_create(
                name=role_data["name"],
                defaults={
                    "description": role_data["description"],
                    "prompt_template": role_data["prompt_template"]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created LLMRole: {role.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'LLMRole already exists: {role.name}'))

        # Display all roles after creation
        self.stdout.write(self.style.SUCCESS('Full list of LLM Roles:'))
        for role in LLMRole.objects.all():
            self.stdout.write(f'- {role.name}: {role.description}')
