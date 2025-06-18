import asyncio
from preprocessing.agent_call import process_file

if __name__ == "__main__":
    file_path = "/Users/zihaomo/Downloads/AI填尽调报告/一个完整例子已填完/3.3 私募管理人及产品尽职调查问卷20221111 (1)_simplified copy.txt"
    results = asyncio.run(process_file(file_path))
    print(results)
