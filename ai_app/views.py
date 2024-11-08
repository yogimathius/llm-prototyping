from venv import logger
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
                {
                    "role": "system",
                    "content": "You are a helpful assistant synthesizing information to answer philosophical questions.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
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
        user_prompt = data.get("prompt")

        if not user_prompt:
            return JsonResponse({"error": "No prompt provided"}, status=400)

        roles = list(LLMRole.objects.all())
        conversation = []
        messages = [
            {
                "role": "system",
                "content": "You are part of a team analyzing input. Respond based on your role. Be concise and specific.",
            }
        ]

        # First turn: only first role responds to user prompt
        first_role = roles[0]
        role_prompt = f"""
        {first_role.prompt_template}

        User Input: {user_prompt}

        Provide a brief, focused analysis in 2-3 sentences.
        """
        messages.append({"role": "system", "content": role_prompt})

        response = get_response(role_prompt, messages)
        if response:
            messages.append({"role": "assistant", "content": response})
            conversation.append(
                {"turn": 1, "role": first_role.name, "response": response}
            )
            print(f"{first_role.name}: {response}\n")
            current_prompt = response  # Store for next role
        else:
            return JsonResponse({"error": "Failed to get initial response"}, status=500)

        # Subsequent turns: each role responds to previous role's response
        for turn in range(1, 4):  # 3 turns
            for role_index, role in enumerate(roles):
                # Skip the first role in the first turn as it's already done
                if turn == 1 and role_index == 0:
                    continue

                role_prompt = f"""
                {role.prompt_template}

                Previous Analysis: {current_prompt}

                Analyze the previous response and provide a brief, focused perspective in 2-3 sentences.
                Focus on building upon or challenging the previous analysis.
                """
                messages.append({"role": "system", "content": role_prompt})

                response = get_response(role_prompt, messages)
                if response:
                    messages.append({"role": "assistant", "content": response})
                    conversation.append(
                        {"turn": turn, "role": role.name, "response": response}
                    )
                    print(f"{role.name}: {response}\n")
                    current_prompt = response  # Update for next role
                else:
                    print(f"Failed to get {role.name} response. Skipping turn.")
                    continue

        # Generate final AI response based on the conversation chain
        analysis = "\n\n".join([
            f"Turn {turn['turn']} - {turn['role']}: {turn['response']}"
            for turn in conversation
        ])
        
        final_analysis_prompt = f"""
        You are an AI assistant tasked with providing a final analysis of a multi-turn conversation between different analytical roles discussing this question:
        
        Original question: "{user_prompt}"
        
        Conversation history:
        {analysis}
        
        Please provide a comprehensive final analysis that:
        1. Summarizes the key points of agreement and disagreement
        2. Identifies the evolution of ideas across turns
        3. Highlights unique insights from each role's perspective
        4. Synthesizes a balanced conclusion
        5. Suggests potential areas for further exploration
        
        Format your response in markdown with the following sections:
        - **Key Points of Agreement**
        - **Notable Disagreements**
        - **Evolution of Discussion**
        - **Unique Insights**
        - **Synthesis**
        - **Further Exploration**
        
        Keep each section concise but insightful. Total response should be under 400 words.
        """

        try:
            final_analysis = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skilled analyst synthesizing a complex discussion. Focus on identifying patterns, key insights, and areas of consensus/disagreement.",
                    },
                    {"role": "user", "content": final_analysis_prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )
            final_response = final_analysis.choices[0].message.content
        except Exception as e:
            logger.error(f"Error occurred while getting final analysis: {e}")
            return JsonResponse({"error": "Failed to generate final analysis"}, status=500)

        if final_response:
            return JsonResponse({
                "original_prompt": user_prompt,
                "conversation": conversation,
                "final_analysis": final_response,
            })
        else:
            return JsonResponse({"error": "Failed to generate final analysis"}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
