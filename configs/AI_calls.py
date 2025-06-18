import asyncio
from config import settings
import logging
from typing import Optional
import json
import requests

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

FASTGPT_API_KEY = settings.FASTGPT_API_KEY
url = settings.FASTGPT_URL

async def extract_answer(response_json):
    content = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
    lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
    data_rows = []
    for line in lines:
        if line.startswith('|') and line.endswith('|') and '---' not in line:
            parts = [part.strip() for part in line.split('|') if part.strip()]
            if len(parts) == 2 and parts[1] != "答案":
                data_rows.append(parts[1])
    if data_rows:
        return data_rows[0]  # Return the first real answer
    return content

async def call_fastgpt(messages, retries=3, **kwargs):
    for attempt in range(retries):
        try:
            headers = {
                "Authorization": f"Bearer {FASTGPT_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "chatId": "000",
                "stream": False,
                "detail": False,
                "messages": [
                    {
                        "role": "user",
                        "content": f"{messages}"
                    }
                ]
            }
            response = requests.post(url, headers=headers, json=data)
            result = await extract_answer(response.json())
            return result
        except Exception as e:
            logger.error(f"Error calling FastGPT: {e}")
    return None
