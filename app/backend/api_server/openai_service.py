import asyncio
import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file.")

client = OpenAI(api_key=api_key)

async def get_openai_response(prompt: str, model="gpt-4o", max_tokens=16000, temperature=0.7) -> str:
    loop = asyncio.get_event_loop()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        completion = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
        )
        print(completion)
        return completion.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"Error contacting OpenAI: {e}")