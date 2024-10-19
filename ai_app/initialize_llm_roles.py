from django.core.management.base import BaseCommand
from ai_app.models import LLMRole

class Command(BaseCommand):
    help = 'Initialize LLM Roles'

    def handle(self, *args, **kwargs):
        data_analyst = LLMRole.objects.create(
            name="Data Analyst",
            description="Analyzes user input to extract key information.",
            prompt_template="""
            You are a Data Analyst.

            Analyze the following user input to identify key focus areas and potential challenges.

            User Input: "{user_input}"

            Provide a brief analysis.
            """
        )
        strategu=LLMRole.objects.create(
            name="Strategist",
            description="Provides strategic insights based on user input.",
            prompt_template="""
            You are a Strategist.

            Analyze the following user input to identify key focus areas and potential challenges.

            User Input: "{user_input}"

            Provide a brief analysis.
            """
        )
        communicator=LLMRole.objects.create(
            name="Communicator",
            description="Provides strategic insights based on user input.",
            prompt_template="""
            You are a Communicator.

            Analyze the following user input to identify key focus areas and potential challenges.

            User Input: "{user_input}"

            Provide a brief analysis.
            """
        )
        self.stdout.write(self.style.SUCCESS(f'Successfully created LLMRole: {data_analyst.name}'))
        self.stdout.write(self.style.SUCCESS(f'Successfully created LLMRole: {strategu.name}'))
        self.stdout.write(self.style.SUCCESS(f'Successfully created LLMRole: {communicator.name}'))