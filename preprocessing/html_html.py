import chardet
import re
import os

def detect_encoding(file_path):
    """自动检测文件编码"""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']

def extract_answers_from_simplified_html(simplified_html_path):
    """从简化HTML文件中提取答案"""
    encoding = detect_encoding(simplified_html_path)
    
    with open(simplified_html_path, 'r', encoding=encoding, errors='ignore') as f:
        lines = f.readlines()
    
    answers_dict = {}
    
    for line in lines:
        # 查找包含绝对编码注释的行
        if '<!-- 绝对编码：3473 -->' in line:
            print("Line with 3473:", repr(line))
        if '<!-- 绝对编码：' in line:
            # 提取绝对编码
            row_match = re.search(r'<!-- 绝对编码：(\d+) -->', line)
            if row_match:
                row_num = int(row_match.group(1))
                
                # 在同一行中查找答案内容
                # 匹配模式：<p>答案内容<o:p></o:p></p> 或类似结构
                answer_patterns = [
                    r'<p>([^<]+)</o:p></p>',  # <p>答案<o:p></o:p></p>
                    r'<p><o:p>([^<]+)</o:p></p>',  # <p>答案<o:p></o:p></p>
                    # r'<p>([^<]+)</p>',             # <p>答案</p>
                    # r'<td>([^<]+)</td>',           # <td>答案</td>
                    # r'>([^<]+)<o:p>',              # >答案<o:p>
                ]
                
                answer = None
                for pattern in answer_patterns:
                    match = re.search(pattern, line)
                    if match:
                        answer = match.group(1).strip()
                        # 过滤掉空答案和特殊字符
                        if answer and answer != '&nbsp;' and answer != '':
                            break
                
                if answer:
                    answers_dict[row_num] = answer
    print("answers_dict[3473]:", answers_dict.get(3473, "Not found"))
    print(f"总共提取到 {len(answers_dict)} 个答案")
    return answers_dict

def fill_html_template(template_html_path, answers_dict, output_html_path):
    """将答案填入HTML模板文件"""
    encoding = detect_encoding(template_html_path)
    
    with open(template_html_path, 'r', encoding=encoding, errors='ignore') as f:
        lines = f.readlines()
    
    filled_count = 0
    
    for i, line in enumerate(lines):
        # 查找包含绝对编码注释的行
        if '<!-- 绝对编码：' in line:
            # 提取绝对编码
            row_match = re.search(r'<!-- 绝对编码：(\d+) -->', line)
            if row_match:
                row_num = int(row_match.group(1))
                
                # 如果有对应的答案
                if row_num in answers_dict:
                    answer = answers_dict[row_num]
                    
                    # 替换空占位符为答案
                    if re.search(r'<o:p>&nbsp;</o:p>', line):
                        lines[i] = re.sub(r'<o:p>&nbsp;</o:p>', f'<o:p>{answer}</o:p>', line)
                        filled_count += 1
                    elif re.search(r'<span[^>]*><o:p>&nbsp;</o:p></span>', line):
                        lines[i] = re.sub(r'<span[^>]*><o:p>&nbsp;</o:p></span>', f'<o:p>{answer}</o:p>', line)
                        filled_count += 1
    
    # 保存结果
    with open(output_html_path, 'w', encoding=encoding) as f:
        f.writelines(lines)
    
    print(f"总共填入 {filled_count} 个答案")
    return filled_count

def html_to_html_fill(simplified_html_path, template_html_path, output_html_path):
    """主函数：从简化HTML提取答案并填入模板HTML"""
    print("=== 开始处理 ===")
    print(f"简化HTML文件：{simplified_html_path}")
    print(f"模板HTML文件：{template_html_path}")
    print(f"输出HTML文件：{output_html_path}")
    
    # 步骤1：从简化HTML中提取答案
    print("\n--- 第1步：提取答案 ---")
    answers_dict = extract_answers_from_simplified_html(simplified_html_path)
    
    # 步骤2：将答案填入模板HTML
    print("\n--- 第2步：填入答案 ---")
    filled_count = fill_html_template(template_html_path, answers_dict, output_html_path)
    
    print(f"\n=== 处理完成 ===")
    print(f"输出文件已保存到: {output_html_path}")
    print(f"成功填入 {filled_count} 个答案")
