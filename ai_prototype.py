import os
from openai import OpenAI

token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4o"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)


# Define roles
role_a = "Assistant"
role_b = "Critic"

# Initial prompts for each role
prompt_a = "You are an assistant helping to write a short story."
prompt_b = "You are a critic reviewing the assistant's work."

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

# Message history for both LLMs
messages = [
    {"role": "system", "content": prompt_a}
]

# Number of turns in the conversation
num_turns = 3

for i in range(num_turns):
    # Assistant's turn
    assistant_response = get_response(prompt_a, messages)
    if assistant_response:
        messages.append({"role": "assistant", "content": assistant_response})
        print(f"Assistant: {assistant_response}\n")
    else:
        print("Failed to get assistant response. Skipping turn.")
        continue

    # Critic's turn
    messages.append({"role": "system", "content": prompt_b})
    critic_response = get_response(prompt_b, messages)
    if critic_response:
        messages.append({"role": "assistant", "content": critic_response})
        print(f"Critic: {critic_response}\n")
    else:
        print("Failed to get critic response. Skipping turn.")
