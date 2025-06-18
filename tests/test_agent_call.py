import logging
from configs.AI_calls import call_fastgpt
from config import settings
import re
from configs.AI_prompts import FASTGPT_PROMPT
import asyncio
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

QUESTION_NUMBER = settings.QUESTION_NUMBER

async def get_answers(questions: dict) -> dict:
    """
    Get answers from FastGPT for a dictionary of questions.
    Returns a dictionary: {line_number: answer}
    """
    logger.info(f"Calling get_answers for {len(questions)} questions.")
    final_answers = {}
    prompt = f"{FASTGPT_PROMPT}\n{questions}"
    answer = await call_fastgpt(prompt)
    logger.info(f"Received answer from FastGPT: {answer}")
    if not answer.strip().startswith("<table>"):
        message_chunks = [chunk.strip() for chunk in answer.split('|||')]
        keys = list(questions.keys())
        message_chunks = [chunk.strip() for chunk in answer.split('|||') if chunk.strip()]
        keys = list(questions.keys())
        for n, chunk in enumerate(message_chunks):
            if chunk == "=":
                continue
            elif n < len(keys):
                key = keys[n]
                final_answers[key] = chunk
                logger.info(f"Mapped answer to line {key}: {chunk}")
            else:
                # Optionally log a warning if there are more answers than questions
                logger.warning(f"More answer chunks than questions: chunk {n} will be ignored.")
                break
        return final_answers
    #for processing tables, return the table answer directly
    else:
        key = list(questions.keys())[0]
        logger.info(f"Mapped table answer to line {key}: {answer}")
        return {key: answer}

async def detect_next_line(file_path: str, line_num: int, answer: str):
    """
    Finds the next line after line_num that contains <!-- 绝对编码：, and replaces the content before <o:p> with the answer.
    Modifies the file in place.
    """
    logger.info(f"Detecting next line with <!-- 绝对编码： after line {line_num} in {file_path}.")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for idx in range(line_num - 1, len(lines)):
        line = lines[idx]
        if '<!-- 绝对编码：' in line:
            # Replace the content inside <o:p>...</o:p> with the answer
            new_line = re.sub(r'<p>.*?</o:p>', f'<p>{answer}</o:p>', line)
            lines[idx] = new_line
            logger.info(f"Replaced content in line {idx} with answer.")
            break
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    logger.info(f"File {file_path} updated with answer.")
    return lines

async def detect_next_line_table(file_path: str, line_num: int, answer: str):
    """
    Finds how many lines the answer spans, and replaces the next n lines in the HTML file
    (starting at line_num) with each line of the answer.
    Modifies the file in place.
    Also parses '\n' in the answer as real newlines and preserves indentation.
    """
    logger.info(f"Detecting next table lines after line {line_num} in {file_path}.")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    # Replace '\n' with real newlines and split into lines
    answer_html = answer.replace('\\n', '\n') if '\\n' in answer else answer.replace('\n', '\n')
    answer_lines = answer_html.split('\n')
    n = len(answer_lines)
    # Determine the indentation of the first line to replace
    indent = ''
    if line_num < len(lines):
        match = re.match(r'(\s*)', lines[line_num])
        if match:
            indent = match.group(1)
    for i in range(n):
        if line_num - 1 + i < len(lines):
            # Add indentation to each line
            lines[line_num - 1 + i] = indent + answer_lines[i].rstrip() + '\n'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    logger.info(f"File {file_path} updated with table answer.")
    return lines

async def process_file(file_path: str):
    """
    Detect all main questions in the given txt file.
    Returns a dictionary: {line_number: question_text}
    Also returns answers as a dictionary: {line_number: answer}
    """
    logger.info(f"Processing file: {file_path}")
    question_pattern = re.compile(
        r'<p>\s*(?!&nbsp;)(.*?)<o:p>', re.UNICODE
    )
    table_pattern = re.compile(r'<table[\s\S]*?</table>', re.IGNORECASE)
    tables_dict = {}
    questions_dict = {}
    table_line_ranges = []  # List of (start_line, end_line) tuples
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        # Find all tables and their start and end line numbers
        for match in table_pattern.finditer(content):
            table_html = match.group(0)
            start_pos = match.start()
            end_pos = match.end()
            start_line = content[:start_pos].count('\n') + 1
            end_line = content[:end_pos].count('\n') + 1
            tables_dict[start_line] = table_html
            table_line_ranges.append((start_line, end_line))
    
    # Now detect questions, skipping lines inside tables
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            # Skip lines that are inside any table
            in_table = any(start <= idx <= end for (start, end) in table_line_ranges)
            if in_table:
                continue
            elif '<!-- 绝对编码：' in line:
                continue
            match = question_pattern.search(line)
            if match:
                question = match.group(1).strip()
                if question == "":
                    continue
                questions_dict[idx] = question
                logger.info(f"Detected question at line {idx}: {question}")

    # Batch the questions into groups of 10 and get answers for each batch
    table_answers = {}
    for line_num, table_html in tables_dict.items():
        table_batch = {line_num: table_html}
        table_answer = await get_answers(table_batch)
        table_answers.update(table_answer)
        
    all_answers = {}
    items = list(questions_dict.items())
    for i in range(0, len(items), QUESTION_NUMBER):
        batch = dict(items[i:i+QUESTION_NUMBER])
        batch_answers = await get_answers(batch)
        # Remove real newlines from each answer
        for key, value in batch_answers.items():
            if isinstance(value, str) and '\n' in value:
                logger.info(f"Removing newlines from answer for line {key}.")
                batch_answers[key] = value.replace('\n', ' ')
        all_answers.update(batch_answers)
        logger.info(f"Processed batch {i // QUESTION_NUMBER + 1} of questions.")
    
    for line_num, answer in all_answers.items():
        await detect_next_line(file_path, line_num, answer)

    for line_num, answer in table_answers.items():
        await detect_next_line_table(file_path, line_num, answer)
    
    logger.info(f"Finished processing file: {file_path}")
    return questions_dict, all_answers

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(__file__), "test_file.txt")
    results = asyncio.run(process_file(file_path))
    print(results)