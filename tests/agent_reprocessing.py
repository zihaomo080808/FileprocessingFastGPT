import asyncio
from preprocessing.html_preprocessing import process_single_file

if __name__ == "__main__":
    file_path = "/Users/zihaomo/Downloads/AI填尽调报告/未填的尽调报告/机构新format/东方财富证券私募类资产管理机构尽职调查报告（XXXX资产管理有限公司）-管理人提供.htm"
    results = process_single_file(file_path)
    print(results)
