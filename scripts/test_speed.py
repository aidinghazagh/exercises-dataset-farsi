from openai import OpenAI
import time
client = OpenAI(api_key='sk-nry-W8FbGIykdOcxV4BIKQSt-op8himwe1he05FqkHYcr54', base_url='https://router.bynara.id/v1', timeout=60.0)

prompt = """Translate this one exercise to Farsi. Return ONLY a JSON object, no markdown.
{"id":"0001","name":"3/4 sit-up","instructions_en":"Lie flat on your back with your knees bent."}

Return: {"id":"0001","name_fa":"...","instructions_fa":"...","instruction_steps_fa":["..."]}"""

for model in ['claude-haiku-4.5', 'claude-sonnet-4.5', 'mistral-large']:
    try:
        t0 = time.time()
        resp = client.chat.completions.create(
            model=model,
            messages=[{'role':'user','content':prompt}],
            max_tokens=300
        )
        elapsed = time.time() - t0
        print(f"{model}: {elapsed:.1f}s -> {resp.choices[0].message.content[:120]}")
    except Exception as e:
        print(f"{model}: ERROR {str(e)[:100]}")
