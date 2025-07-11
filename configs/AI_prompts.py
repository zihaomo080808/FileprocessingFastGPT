from config import settings

QUESTION_NUMBER = settings.QUESTION_NUMBER

FASTGPT_PROMPT = f"""
任务目标：填写海南盖亚青柯私募基金管理有限公司的尽职调查问卷，按章节顺序逐步完成所有空白字段的填写  

你必须区分以下两种情况：

1. 我给你一个提问列表，比如：
{{238: '表格  SEQ 表格 \* ARABIC 2:联系方式', 270: '2.   请说明公司整体的优势和劣势分别是什么，以及维持优势的关键因素。', 273: '3.   请说明公司近三年的基本财务状况（万元）。', 378: '4.   请填写下表的股权结构（须穿透至实际控制人）。'}}
前面的数字是行数，后面的文字是问题（我会给你{QUESTION_NUMBER}个问题）。


2. 我给你一个简化过的需要填写的表格（通过 <tr>...</tr> 标签表示）。
e.g. 输入
<tr>\\n ...\\n </tr>

如果识别为第一种情况，仅返回对于问题的答案。按照以下步骤返回答案：
1. 如果检测到某一个内容不是需要填写的信息，或者看到的是一个''的空字符，那么用一个“=”字符代替
2. 如果问题是开放性的、或者没有提供原始数据，或者没有足够信息已回答，请基于常见私募基金管理公司的情况自动生成合理答案，不要留下空白或填“=”。然后，在答案的最后面加一个括号：“（请根据实际情况填写）”
3. 如果问题中包含很多子问题，你必须细致回答每一个能回答的问题。
4. 最后按照以下格式分隔然后输出，使用符号 ||| 分隔答案（中间不加空格）：
"答案1|||答案2|||答案3|||...|||答案{QUESTION_NUMBER}"

不要用1. 2. 3. 等序号。严格按照我给你的格式回答

如果识别为第二种情况，按以下规则填写表格, 识别表格中的问题格式, 识别表格的格式, 按照表格格式填写内容。

填写表格时的具体规则：
1. 将所有 &nbsp; 替换为对应的答案。你要去识别表格中空格对应的问题，然后回答问题。
2. 不要删除表格中的任何信息。
3. 不要添加任何额外信息到表格中。
4. 不要改变表格中问题的顺序。
5. 不要改变表格中问题的格式。
6. 不要改变表格中答案的格式。
7. 不要改变表格的格式。
8. 当检测到"\\n"的时候请保留这两个个符号
9. 保留绝对编码
10. 输出的时候返回表格不要时真正的html格式，而是用\\n来分隔每一行。
11. □ 如果遇到这类符号，用☑来替代正确勾选的答案，如果没有那么返回原来的符号。

e.g. 输出
<tr>\\n 职务\\n xxx <!-- 绝对编码：2607 -->\\n ...\\n </tr>

真正输入：
"""

ERROR_PROMPT = f"""
按以下规则填写表格, 识别表格中的问题格式, 识别表格的格式, 按照表格格式填写内容。

填写表格时的具体规则：
1. 将所有 &nbsp; 替换为对应的答案。你要去识别表格中空格对应的问题，然后回答问题。
2. 不要删除表格中的任何信息。
3. 不要添加任何额外信息到表格中。
4. 不要改变表格中问题的顺序。
5. 不要改变表格中问题的格式。
6. 不要改变表格中答案的格式。
7. 不要改变表格的格式。
8. 当检测到"\\n"的时候请保留这两个个符号
9. 保留绝对编码
10. 输出的时候返回表格应该有的HTML格式。

e.g. 输出
<tr>\\n 职务\\n...\\n </tr>

"""