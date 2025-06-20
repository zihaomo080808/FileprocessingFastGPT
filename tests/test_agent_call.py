import logging
from configs.AI_calls import call_fastgpt
from config import settings
import re
from configs.AI_prompts import FASTGPT_PROMPT, ERROR_PROMPT
import asyncio
import os
import tiktoken
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

logger = logging.getLogger(__name__)

QUESTION_NUMBER = settings.QUESTION_NUMBER

def count_tokens(text, model="gpt-3.5-turbo"):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

async def process_table_before_call(table_html: str, start_row: int, max_tokens=1000, model="gpt-3.5-turbo"):

    tr_blocks = re.findall(r'(<tr[\s\S]*?</tr>)', table_html, re.IGNORECASE)
    preserved_rows = []

    for tr in tr_blocks:
        tr_tag = re.match(r'<tr[^>]*>', tr, re.IGNORECASE)
        tr_start = tr_tag.group(0) if tr_tag else '<tr>'
        tr_end = '</tr>'

        # Remove the <tr> and </tr> tags for cell processing
        tr_inner = re.sub(r'^<tr[^>]*>', '', tr, flags=re.IGNORECASE)
        tr_inner = re.sub(r'</tr>$', '', tr_inner, flags=re.IGNORECASE)

        # Find all <td>...</td> blocks
        td_blocks = re.findall(r'(<td[\s\S]*?</td>)', tr_inner, re.IGNORECASE)
        processed_cells = []
        if td_blocks:
            for td in td_blocks:
                allowed = []
                nbsps = re.findall(r'&nbsp;', td)
                codes = re.findall(r'<!--\s*绝对编码：.*?-->', td)
                seen_codes = set()
                unique_codes = []
                for code in codes:
                    if code not in seen_codes:
                        unique_codes.append(code)
                        seen_codes.add(code)
                text = re.sub(r'<[^>]+>', '', td)
                text = text.replace('&nbsp;', '').strip()
                if text:
                    allowed.append(text)
                allowed.extend(nbsps)
                allowed.extend(unique_codes)
                if allowed:
                    processed_cells.append('  ' + ' '.join(allowed) + '\n')  # Add newline after each cell
        else:
            lines = tr_inner.splitlines()
            for line in lines:
                allowed = []
                codes = re.findall(r'<!--\s*绝对编码：.*?-->', line)
                seen_codes = set()
                unique_codes = []
                for code in codes:
                    if code not in seen_codes:
                        unique_codes.append(code)
                        seen_codes.add(code)
                text = re.sub(r'<[^>]+>', '', line).strip()
                if text:
                    allowed.append(text)
                allowed.extend(unique_codes)
                if allowed:
                    processed_cells.append('  ' + ' '.join(allowed) + '\n')  # Add newline after each line
        content = ''.join(processed_cells)  # No join with \n, as each already ends with \n
        preserved_rows.append(f"{tr_start}\n{content}{tr_end}")

    # Now chunk the table if too long
    chunks = []  # Each element: (chunk_string, start_row_index)
    current_chunk = []
    current_tokens = 0
    current_start_row = start_row
    for i, row in enumerate(preserved_rows):
        row_tokens = count_tokens(row, model=model)
        if current_tokens + row_tokens > max_tokens and current_chunk:
            # Start a new chunk
            chunks.append(('\n'.join(current_chunk), current_start_row))
            current_chunk = []
            current_tokens = 0
            current_start_row = i + 1  # Next chunk starts at this row (1-based)
        current_chunk.append(row)
        current_tokens += row_tokens

    if current_chunk:
        chunks.append(('\n'.join(current_chunk), current_start_row))

    return chunks

async def process_table_after_call(original_file_path: str, line_num: int, ai_table: str):
    # Build a mapping from code to answer from the ai_table
    ai_rows = re.findall(r'<tr>([\s\S]*?)</tr>', ai_table, re.IGNORECASE)
    code_to_answer = {}

    for row in ai_rows:
        for code_match in re.finditer(r'<!--\s*绝对编码：(\d+)\s*-->', row):
            code = code_match.group(1)
            before_code = row[:code_match.start()]
# Remove comments
            before_code = re.sub(r'<!--.*?-->', '', before_code)
            # Remove tags
            before_code = re.sub(r'<[^>]+>', '', before_code)
            # Split by newlines and get the last non-empty, stripped line
            lines_before = before_code.split('\n')
            answer = ''
            for line in reversed(lines_before):
                stripped = line.strip()
                if stripped:
                    answer = stripped
                    break
            answer = answer.replace('&nbsp;', '').strip()
            if answer:
                code_to_answer[code] = answer
            else:
                print(f"No answer extracted for code {code} in row: {row}")

    # 2. Read the original file
    with open(original_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 3. Loop from line_num to the next </table>
    idx = line_num - 1  # line_num is 1-based
    while idx < len(lines):
        line = lines[idx]
        if '</table>' in line:
            break
        code_match = re.search(r'<!--\s*绝对编码：(\d+)\s*-->', line)
        if code_match:
            code = code_match.group(1)
            answer = code_to_answer.get(code)
            if answer:
                print(f"Replacing in line {idx}: {line.strip()} with answer: {answer}")
                lines[idx] = re.sub(
                    r'(<p>)(.*?)(<o:p>)',
                    lambda m: m.group(1) + answer + m.group(3),
                    line,
                    count=1
                )
            else:
                print(f"No answer found in ai_table for code {code}")
        idx += 1

    with open(original_file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return lines

async def process_answers(questions: dict, answer: str, start_row: Optional[int] = None):
    final_answers = {}
    if not answer.strip().startswith("<tr>"):
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
        return {start_row: answer}


async def get_answers(questions: dict) -> dict:
    logger.info(f"Calling get_answers for {len(questions)} questions.")
    final_answers = {}
    # If questions is a dict with a single value that starts with <table>, preprocess it
    if isinstance(questions, dict) and len(questions) == 1:
        only_value = next(iter(questions.values()))
        if isinstance(only_value, str) and only_value.strip().startswith('<table>'):
            start_row = next(iter(questions.keys()))
            questions_modified = await process_table_before_call(only_value, start_row)
            for chunk, start_row in questions_modified:
                prompt = f"{FASTGPT_PROMPT}\n{chunk}"
                answer = await call_fastgpt(prompt)
                logger.info(f"Received answer from FastGPT: {answer}")
                final_answers.update(await process_answers(questions, answer, start_row))
        else:
            prompt = f"{FASTGPT_PROMPT}\n{questions}"
            answer = await call_fastgpt(prompt)
            logger.info(f"Received answer from FastGPT: {answer}")
            final_answers = await process_answers(questions, answer)
    else:
        prompt = f"{FASTGPT_PROMPT}\n{questions}"
        answer = await call_fastgpt(prompt)
        logger.info(f"Received answer from FastGPT: {answer}")
        final_answers = await process_answers(questions, answer)
    return final_answers

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

async def get_answers_concurrent(batches, max_concurrent=10):
    """
    batches: list of dicts, each dict is a batch of questions {line_number: question}
    max_concurrent: max number of concurrent AI calls
    Returns: list of dicts (answers for each batch)
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    async def sem_task(batch):
        async with semaphore:
            logger.info(f"Starting AI call for batch of size {len(batch)}")
            return await get_answers(batch)
    tasks = [asyncio.create_task(sem_task(batch)) for batch in batches]
    return await asyncio.gather(*tasks)

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

    # Batch the tables into single-item dicts and get answers for each batch concurrently
    table_batches = [{line_num: table_html} for line_num, table_html in tables_dict.items()]
    table_answers = {}
    if table_batches:
        table_answers_list = await get_answers_concurrent(table_batches, max_concurrent=10)
        for table_answer in table_answers_list:
            table_answers.update(table_answer)
        logger.info(f"Processed all table batches concurrently.")
    
    all_answers = {}
    items = list(questions_dict.items())
    batches = [dict(items[i:i+QUESTION_NUMBER]) for i in range(0, len(items), QUESTION_NUMBER)]
    if batches:
        batch_answers_list = await get_answers_concurrent(batches, max_concurrent=10)
        for batch_answers in batch_answers_list:
            for key, value in batch_answers.items():
                if isinstance(value, str) and '\n' in value:
                    logger.info(f"Removing newlines from answer for line {key}.")
                    value = value.replace('\n', ' ')
                all_answers[key] = value
        logger.info(f"Processed all batches of questions concurrently.")
    
    for line_num, answer in all_answers.items():
        await detect_next_line(file_path, line_num, answer)

    for line_num, answer in table_answers.items():
        await process_table_after_call(file_path, line_num, answer)
    
    logger.info(f"Finished processing file: {file_path}")
    return questions_dict, all_answers

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(__file__), "test_file.txt")
    results = asyncio.run(process_file(file_path))
    print(results)