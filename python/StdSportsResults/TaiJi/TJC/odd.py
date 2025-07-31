import json

def extract_odd_lines(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        lines = infile.readlines()
        for i, line in enumerate(lines, start=1):
            if i % 2 != 0:  # 奇数行
                # 验证是否为有效的JSON行
                try:
                    json.loads(line.strip())
                    outfile.write(line)
                except json.JSONDecodeError:
                    print(f"跳过第 {i} 行：无效的JSON格式")

# 使用示例
input_filename = './LearningMode/all.json'  # 替换为你的输入文件名
output_filename = './LearningMode/odd.json'  # 输出文件名

extract_odd_lines(input_filename, output_filename)
print(f"奇数行已提取并保存到 {output_filename}")
