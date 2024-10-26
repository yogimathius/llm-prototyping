from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import os
from ai_app.models import LLMRole
from openai import OpenAI

# Create your views here.

# Assuming you've set these in your environment variables
token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4o"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

def get_response(prompt, message_history):
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=message_history,
            temperature=1.0,
            top_p=1.0,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error occurred while getting response: {e}")
        return None

def get_ai_response(analysis, original_prompt):
    prompt = f"""
    You are an AI assistant tasked with synthesizing an analysis and crafting a response to a user's question about the meaning of life. 
    
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

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant synthesizing information to answer philosophical questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error occurred while getting AI response: {e}")
        return None

@csrf_exempt
@require_POST
def receive_prompt(request):
    try:
        data = json.loads(request.body)
        user_prompt = data.get('prompt')
        
        if not user_prompt:
            return JsonResponse({'error': 'No prompt provided'}, status=400)
        
        roles = list(LLMRole.objects.all())
        conversation = []
        messages = [
            {"role": "system", "content": "You are part of a team analyzing a user's input. Respond based on your specific role."},
            {"role": "user", "content": f"User Input: {user_prompt}"}
        ]

        num_turns = 3  # Number of turns for each role

        for i in range(num_turns):
            for role in roles:
                role_prompt = f"{role.prompt_template}\n\nUser Input: {user_prompt}\n\nProvide your analysis:"
                messages.append({"role": "system", "content": role_prompt})
                
                response = get_response(role_prompt, messages)
                if response:
                    messages.append({"role": "assistant", "content": response})
                    conversation.append({
                        'turn': i + 1,
                        'role': role.name,
                        'response': response
                    })
                    print(f"{role.name}: {response}\n")
                else:
                    print(f"Failed to get {role.name} response. Skipping turn.")
                    continue

        # Generate AI response based on the analysis
        analysis = "\n\n".join([f"{turn['role']}: {turn['response']}" for turn in conversation])
        ai_response = get_ai_response(analysis, user_prompt)

        if ai_response:
            return JsonResponse({
                'original_prompt': user_prompt,
                'conversation': conversation,
                'ai_response': ai_response
            })
        else:
            return JsonResponse({'error': 'Failed to generate AI response'}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
