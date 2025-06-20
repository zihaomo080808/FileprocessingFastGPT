from tests.test_agent_call import process_table_before_call
import asyncio

async def main():
    simplified_html = "tests/test_file.txt"
    with open(simplified_html, "r") as f:
        simplified_html_content = f.read()
    processed_html_content = await process_table_before_call(simplified_html_content)
    print(processed_html_content)

if __name__ == "__main__":
    asyncio.run(main())

