import litellm
import os

print("ENV keys with API/KEY/GEMINI/GOOGLE:", {k: '***' for k in os.environ if 'API' in k or 'KEY' in k or 'GEMINI' in k or 'GOOGLE' in k})

try:
    response = litellm.completion(
        model="gemini/gemini-1.5-flash",
        messages=[{"role": "user", "content": "Hello! Reply with 'OK' if you can read this."}]
    )
    print("Success with gemini-1.5-flash!")
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("Failed with gemini-1.5-flash:", e)

try:
    response = litellm.completion(
        model="gemini/gemini-2.5-flash",
        messages=[{"role": "user", "content": "Hello! Reply with 'OK' if you can read this."}]
    )
    print("Success with gemini-2.5-flash!")
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("Failed with gemini-2.5-flash:", e)
