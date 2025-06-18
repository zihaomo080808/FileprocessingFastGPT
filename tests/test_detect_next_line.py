import logging
import re
import asyncio
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


async def detect_next_line(file_path: str, line_num: int, answer: str):
    """
    Finds the next line after line_num that contains <!-- 绝对编码：, and replaces the content before <o:p> with the answer.
    Modifies the file in place.
    """
    logger.info(f"Detecting next line with <!-- 绝对编码： after line {line_num} in {file_path}.")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for idx in range(line_num, len(lines)):
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


async def main():
    questions = {220: '5. 请提供公司历史股权及高管（包括实际控制人、控股股东及法定代表人\执行事务合伙人（委派代表））变更情况；如有变更的，请说明对公司的影响。', 222: '6. 请提供公司历史简介以及发展进程中的重大事件。请说明公司股票是否上市或公开挂牌交易，如是，请说明上市挂牌的交易所、时间。', 224: '7. 请提供公司所有分支（或子公司）、同一控制人下的关联公司的名称以及主营范围。', 225: '如有从事无资管业务关联方，请说明名称、业务范围，和公司的业务和定位差异，设立目的，是否根据基金业协会要求开展集团化私募基金管理机构自查，关联方旗下基金之间是否进行相互嵌套，是否存在连带风险，是否建立公平交易、利益冲突防范机制？', 226: '请说明关联方业务是否与公司业务存在利益冲突（如民间借贷、民间融资、配资业务、小额理财、小额借贷、P2P/P2B、众筹、保理、担保、房地产开发、交易平台、自营投资等），如有，是否已建立利益冲突防范机制？', 228: '8. 请说明公司的长期经营规划，以及未来1年的基金募集规划。'}
    answer = "公司成立于2021年，历史股权及高管未发生变更，对公司无重大影响（请根据实际情况填写）|||公司历史简介：海南盖亚青柯私募基金管理有限公司成立于2021年，主要从事私募证券投资基金管理服务。公司股票未上市或公开挂牌交易（请根据实际情况填写）|||子公司及主要关联方：深圳市盖亚青柯技术有限公司 海南盖亚青柯技术合伙企业（有限合伙）|||无资管业务关联方，关联方业务与公司业务无利益冲突，已建立公平交易和利益冲突防范机制（请根据实际情况填写）|||关联方业务与公司业务无利益冲突，已建立利益冲突防范机制（请根据实际情况填写）|||计划初步建立资管规模，2025年目标总规模20亿，三年内目标总规模50亿"
    all_answers = {}
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
                all_answers[key] = chunk
                logger.info(f"Mapped answer to line {key}: {chunk}")
            else:
                # Optionally log a warning if there are more answers than questions
                logger.warning(f"More answer chunks than questions: chunk {n} will be ignored.")
                break
    #for processing tables, return the table answer directly
    file_path = os.path.join(os.path.dirname(__file__), "test_file.txt")
    for line_num, answer in all_answers.items():
        await detect_next_line(file_path, line_num, answer)

if __name__ == "__main__":
    asyncio.run(main())