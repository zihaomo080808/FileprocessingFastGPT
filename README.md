尽调报告预处理工具
功能：1. 添加绝对编码注释 2. 清理HTML结构
使用示例
1. 批量处理（两步都执行）:
python run.py *.htm

2. 只添加绝对编码：
python run.py *.htm -s 1

3. 处理单个文件：
python run.py input.htm

4. 处理多个指定文件：
python run.py file1.htm file2.htm file3.htm

提示：如果要使用配置模式，请将 USE_CONFIG_MODE 设置为 True