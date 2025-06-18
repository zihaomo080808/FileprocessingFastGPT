import sys
import argparse
import os
import shutil
import asyncio
from config import settings
from configs.files_to_process import FILES_TO_PROCESS
from preprocessing.html_preprocessing import process_single_file, find_files
from preprocessing.agent_call import process_file
from preprocessing.html_html import html_to_html_fill

PROCESS_BOTH_STEPS = settings.PROCESS_BOTH_STEPS
USE_CONFIG_MODE = settings.USE_CONFIG_MODE

async def run_agent_on_file(simplified_file):
    # Make a copy for agent processing
    base_name, extension = os.path.splitext(simplified_file)
    agent_file = f"{base_name}_copy{extension}"
    shutil.copyfile(simplified_file, agent_file)
    print(f"Copied {simplified_file} to {agent_file}")
    # Run the async agent on the copy
    await process_file(agent_file)
    print(f"Agent processing complete for {agent_file}")
    return agent_file

def process_and_run_agent(input_file, process_both_steps=True):
    # Step 1: Preprocess and create simplified file
    simplified_file = process_single_file(input_file, process_both_steps)
    # Step 2: Find the simplified file name
    base_name, extension = os.path.splitext(input_file)
    # Step 3: Run the async agent on the copy
    agent_file = asyncio.run(run_agent_on_file(simplified_file))
    template_html = f"{base_name}_with_comments{extension}"
    output_html = f"{base_name}_final_filled.html"
    html_to_html_fill(agent_file, template_html, output_html)
    print(f"Final filled HTML saved to: {output_html}")

def run_config_mode():
    print("=== 尽调报告预处理工具 - 配置模式运行 ===")
    print(f"要处理的文件数量: {len(FILES_TO_PROCESS)}")
    print(f"处理步骤: {'两步都执行' if PROCESS_BOTH_STEPS else '只执行第一步（添加绝对编码）'}")
    print("\n开始处理...")
    success_count = 0
    for file_path in FILES_TO_PROCESS:
        try:
            process_and_run_agent(file_path, PROCESS_BOTH_STEPS)
            success_count += 1
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {str(e)}")
            continue
    print(f"\n处理完成！成功处理 {success_count}/{len(FILES_TO_PROCESS)} 个文件")

def main():
    parser = argparse.ArgumentParser(description='尽调报告预处理工具')
    parser.add_argument('files', nargs='+', help='输入文件路径（支持通配符）')
    parser.add_argument('-s', '--steps', choices=['1', '2', 'both'], default='both',
                       help='处理步骤：1=只添加绝对编码, 2=只清理HTML, both=两步都执行（默认）')
    args = parser.parse_args()
    all_files = []
    for pattern in args.files:
        found_files = find_files(pattern)
        if found_files:
            all_files.extend(found_files)
        else:
            print(f"警告：未找到匹配的文件: {pattern}")
    if not all_files:
        print("错误：没有找到要处理的文件")
        sys.exit(1)
    print(f"找到 {len(all_files)} 个文件需要处理")
    for file_path in all_files:
        try:
            process_both = args.steps == 'both'
            process_and_run_agent(file_path, process_both)
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {str(e)}")
            continue
    print("所有文件处理完成！")

if __name__ == "__main__":
    if USE_CONFIG_MODE:
        run_config_mode()
    else:
        if len(sys.argv) == 1:
            print("请看readme.md文件")
            sys.exit(0)
        main()
