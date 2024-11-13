from transformers import T5Tokenizer, T5ForConditionalGeneration
import logging

logger = logging.getLogger("ai_app")


class AIHandler:
    def __init__(self):
        try:
            self.tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-large")
            self.model = T5ForConditionalGeneration.from_pretrained(
                "google/flan-t5-large"
            )

        except Exception as e:
            logger.error(f"Error initializing AIHandler: {str(e)}")
            raise

    def get_role_response(self, role, user_prompt):
        try:
            input_ids = self.tokenizer(
                user_prompt,
                return_tensors="pt",
            ).input_ids

            outputs = self.model.generate(
                input_ids,
            )

            response = self.tokenizer.decode(outputs[0])

            logger.debug(f"Generated response: {response}")
            return response

        except Exception as e:
            logger.error(f"Error in get_role_response: {str(e)}")
            return None
