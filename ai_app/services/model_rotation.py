from openai import OpenAI
import os
import logging

logger = logging.getLogger("ai_app")


class OpenAIService:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=os.getenv("GITHUB_TOKEN"),
        )
        self.model_name = "gpt-4o-mini"

    def create_completion(self, messages, temperature=0.7, max_tokens=1000, top_p=1.0):
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in completion: {e}")
            raise
