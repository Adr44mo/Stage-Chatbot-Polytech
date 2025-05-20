from groq import Groq

client = Groq(api_key="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")

model = "meta-llama/llama-4-scout-17b-16e-instruct"

print("Chatbot is ready! Type 'exit' to quit.")

while True:
    user_input = input("\nYou: ")
    if user_input.lower() == "exit":
        break

    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_input}],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )

    print("Bot: ", end="", flush=True)
    for chunk in completion:
        print(chunk.choices[0].delta.content or "", end="", flush=True)
    print()