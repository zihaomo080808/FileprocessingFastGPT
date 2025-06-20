from tests.test_agent_call import process_table_after_call
import asyncio

async def main():
    simplified_html = "tests/test_file.txt"
    line_num = 1
    with open("tests/test_file2.txt", "r", encoding="utf-8") as f:
        answer = f.read()
    processed_html_content = await process_table_after_call(simplified_html, line_num, answer)
    print(processed_html_content)

if __name__ == "__main__":
    asyncio.run(main())

