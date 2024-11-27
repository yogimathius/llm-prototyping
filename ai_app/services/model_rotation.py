from openai import OpenAI
from ollama import chat
import os
import logging

logger = logging.getLogger("ai_app")


class OpenAIService:
    def __init__(self, use_ollama=False, model_name=None):
        self.use_ollama = use_ollama
        self.model_name = model_name or ("llama3.2" if use_ollama else "gpt-4o-mini")
        if not use_ollama:
            self.client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=os.getenv("GITHUB_TOKEN"),
            )

    def create_completion(self, messages, temperature=0.7, max_tokens=1000, top_p=1.0):
        try:
            if self.use_ollama:
                response_stream = chat(
                    model=self.model_name, messages=messages, stream=True
                )

                full_response = ""
                for chunk in response_stream:
                    if chunk and "message" in chunk and "content" in chunk["message"]:
                        content = chunk["message"]["content"]
                        full_response += content
                        print(content, end="", flush=True)

                return full_response
            else:
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

    def create_streaming_completion(self, messages, temperature=0.7, max_tokens=1000):
        """Separate method for streaming responses"""
        try:
            if self.use_ollama:
                stream = chat(
                    model="llama2",
                    messages=messages,
                    stream=True,
                )
                for chunk in stream:
                    yield chunk["message"]["content"]
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Error in streaming completion: {e}")
            raise
