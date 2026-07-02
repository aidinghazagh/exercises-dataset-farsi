from httpx_socks import SyncProxyTransport
import httpx, time
from openai import OpenAI

transport = SyncProxyTransport.from_url("socks5://127.0.0.1:10808")
http_client = httpx.Client(transport=transport, timeout=60.0)
client = OpenAI(
    api_key="sk-nry-mVIeH3waFo2XVyi4ZaJPzT6B5whOBiQWfnFT6m3iWnk",
    base_url="https://router.bynara.id/v1",
    http_client=http_client
)

prompt = (
    'Translate this exercise to Farsi. Return ONLY a JSON object, no markdown.\n'
    '{"id":"0025","name":"barbell bench press",'
    '"instructions_en":"Lie on a flat bench with feet on the floor. Grip the bar slightly wider than shoulder width. Unrack and lower to mid-chest. Press up explosively.",'
    '"steps_en":["Lie on a flat bench.","Grip the bar wider than shoulders.","Lower to mid-chest.","Press back up."]}\n'
    'Return: {"id":"0025","name_fa":"...","instructions_fa":"...","instruction_steps_fa":["...","...","...","..."]}'
)

for model in ["mistral-large", "mistral-medium-3-5"]:
    times = []
    for attempt in range(3):
        try:
            t0 = time.time()
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            elapsed = time.time() - t0
            times.append(elapsed)
            content = resp.choices[0].message.content[:120]
            print(f"{model} attempt {attempt+1}: {elapsed:.1f}s -> {content}")
            time.sleep(3)
        except Exception as e:
            print(f"{model} attempt {attempt+1}: ERROR {str(e)[:80]}")
            time.sleep(5)
    if times:
        print(f"{model} avg: {sum(times)/len(times):.1f}s (min: {min(times):.1f}s, max: {max(times):.1f}s)")
    print()
