import asyncio
from configs.AI_calls import call_fastgpt

async def test_call_fastgpt():
    response = await call_fastgpt("年收入是多少")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_call_fastgpt())