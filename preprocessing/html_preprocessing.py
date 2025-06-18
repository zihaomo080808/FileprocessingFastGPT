"""

配置文件在configs/files_to_process.py

尽调报告预处理工具
功能：
1. 添加绝对编码注释到HTML文件 (生成 _with_comments.htm)
2. 清理HTML文件结构 (生成 _simplified.txt)

支持批量处理多个文件
"""

import argparse
import chardet
import os
import re
import sys
from pathlib import Path
import glob
from config import settings
from configs.files_to_process import FILES_TO_PROCESS

# 是否执行两步处理（True=两步都执行，False=只执行第一步添加绝对编码）在.env里面改
PROCESS_BOTH_STEPS = settings.PROCESS_BOTH_STEPS

# 是否使用配置文件模式（True=使用上面的配置，False=使用命令行参数）
USE_CONFIG_MODE = settings.USE_CONFIG_MODE

def detect_encoding(file_path):
    """自动检测文件编码"""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']


def add_line_number_to_o_p(htm_file):
    """
    给HTML文件中包含<o:p>&nbsp;</o:p>的行添加绝对编码注释
    """
    # 自动检测编码
    encoding = detect_encoding(htm_file)
    print(f"文件编码为: {encoding}")

    # 读取HTM文件内容
    with open(htm_file, 'r', encoding=encoding, errors='ignore') as file:
        lines = file.readlines()

    # 逐行处理，只在符合条件时增加注释
    processed_lines = []
    for line_number, line in enumerate(lines, 1):
        if '<o:p>&nbsp;</o:p>' in line:
            # 在包含 <o:p>&nbsp;</o:p> 的行末尾添加注释
            line = line.rstrip() + f" <!-- 绝对编码：{line_number} -->\n"
        processed_lines.append(line)

    # 返回修改后的内容
    return ''.join(processed_lines), encoding


def clean_html(htm_file):
    """
    清理HTML文件，删除特定标签和属性
    """
    # 自动检测编码
    encoding = detect_encoding(htm_file)
    print(f"文件编码为: {encoding}")

    # 读取HTM文件内容
    with open(htm_file, 'r', encoding=encoding, errors='ignore') as file:
        html_content = file.read()

    # 定义需要完全删除的标签列表
    tags_to_remove = ['span', 'a', 'b', 'i', '!']
    
    # 定义需要简化属性（只保留标签名）的标签列表
    tags_to_simplify = ['table', 'p', 'div', 'html', 'h1', 'h2', 'h3', 'h4', 'h5', 'td', 'tr']

    html_content = re.sub(r'<w:data[^>]*>.*?</w:data>', '', html_content, flags=re.DOTALL)

    html_content = re.sub(r'<!-- 绝对编码', '<8888!-- 绝对编码', html_content)
    
    # 处理需要完全删除的标签
    for tag in tags_to_remove:
        # 删除开始标签及其属性
        html_content = re.sub(fr'<{tag}[^>]*>', '', html_content, flags=re.IGNORECASE)
        # 删除结束标签
        html_content = html_content.replace(f'</{tag}>', '')
        html_content = html_content.replace(f'</{tag.upper()}>', '')  # 处理大写标签

    html_content = re.sub(r'<8888!-- 绝对编码', '<!-- 绝对编码', html_content)

    # 处理需要简化属性的标签
    for tag in tags_to_simplify:
        # 将开始标签替换为简单形式（去掉属性）
        html_content = re.sub(fr'<{tag}[^>]*>', f'<{tag}>', html_content, flags=re.IGNORECASE)

    # 处理<head>部分 - 保留<head>和</head>标签，只清空中间内容但保留行数
    html_content = re.sub(r'(<head[^>]*>)(.*?)(</head>)', 
                         lambda m: m.group(1) + '\n' * m.group(2).count('\n') + m.group(3), 
                         html_content, 
                         flags=re.DOTALL | re.IGNORECASE)

    # 删除空行
    html_content = '\n'.join([line for line in html_content.splitlines() if line.strip()])

    return html_content


def process_single_file(input_file, process_both_steps=True):
    """
    处理单个文件
    """
    print(f"\n正在处理文件: {input_file}")
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：文件不存在 - {input_file}")
        return None
    
    # 获取文件路径信息
    base_name, extension = os.path.splitext(input_file)
    
    # 第一步：添加绝对编码
    print("步骤1: 添加绝对编码注释...")
    output_file_step1 = f"{base_name}_with_comments{extension}"
    
    try:
        content, encoding = add_line_number_to_o_p(input_file)
        with open(output_file_step1, 'w', encoding=encoding) as file:
            file.write(content)
        print(f"✓ 步骤1完成，输出文件: {output_file_step1}")
    except Exception as e:
        print(f"✗ 步骤1失败: {str(e)}")
        return None
    
    # 第二步：清理HTML（如果需要）
    if process_both_steps:
        print("步骤2: 清理HTML结构...")
        
        # 生成简化文件名
        dir_name = os.path.dirname(input_file)
        file_name = os.path.basename(input_file)
        simplified_name = file_name.replace('_with_comments', '')
        simplified_name = os.path.splitext(simplified_name)[0] + '_simplified.txt'
        output_file_step2 = os.path.join(dir_name, simplified_name)
        
        try:
            content = clean_html(output_file_step1)
            with open(output_file_step2, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"✓ 步骤2完成，输出文件: {output_file_step2}")
            return output_file_step2
        except Exception as e:
            print(f"✗ 步骤2失败: {str(e)}")
    else:
        return output_file_step1


def find_files(pattern):
    """
    根据模式查找文件
    """
    if os.path.isfile(pattern):
        return [pattern]
    else:
        return glob.glob(pattern)