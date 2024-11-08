import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from django.conf import settings

class AIHandler:
    def __init__(self, model_name="gpt2"):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        # Set the pad token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model.config.pad_token_id = self.tokenizer.eos_token_id

    def get_response(self, prompt, max_new_tokens=100):
        inputs = self.tokenizer.encode_plus(
            prompt,
            add_special_tokens=True,
            return_tensors="pt",
            padding='max_length',
            max_length=512,  # Increased to accommodate longer prompts
            truncation=True,
        )
        
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                num_return_sequences=1,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the input prompt from the response
        response = response[len(self.tokenizer.decode(input_ids[0], skip_special_tokens=True)):].strip()
        return response

    def get_role_response(self, role, user_prompt):
        role_prompt = f"{role.prompt_template}\n\nUser Input: {user_prompt}\n\nProvide your analysis:"
        return self.get_response(role_prompt, max_new_tokens=200)

    def get_ai_response(self, analysis, original_prompt):
        prompt = f"""
        You are an AI assistant tasked with synthesizing an analysis and crafting a response to a user's question. 
        
        Original user question: "{original_prompt}"
        
        Analysis from multiple perspectives:
        {analysis}
        
        Based on this analysis, craft a thoughtful, engaging, and concise response to the user's original question. The response should:
        1. Acknowledge the complexity and subjectivity of the question
        2. Offer multiple perspectives (e.g., philosophical, scientific, cultural)
        3. Encourage personal reflection
        4. Maintain an open and inclusive tone
        5. Invite the user to continue their own exploration of the topic
        
        Your response should be written in markdown format for easy formatting.
        """

        return self.get_response(prompt, max_new_tokens=500)
