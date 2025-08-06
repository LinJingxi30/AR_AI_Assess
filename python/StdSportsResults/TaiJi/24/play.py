import json

def modify_json(input_file, output_file, prefix):
    """
    读取 JSON 文件，修改 'image' 字段前添加指定字符，并保存到新的 JSON 文件。

    :param input_file: 输入的 JSON 文件路径
    :param output_file: 输出的 JSON 文件路径
    :param prefix: 要添加到 'image' 字段前的字符
    """
    with open(input_file, 'r', encoding='utf-8') as fin:
        lines = fin.readlines()

    modified_data = []

    for line in lines:
        # 解析 JSON 数据
        record = json.loads(line.strip())
        
        # 修改 'image' 字段，添加前缀
        record['image'] = prefix + record['image']
        
        # 将修改后的记录添加到新列表中
        modified_data.append(record)

    # 保存修改后的数据到新文件
    with open(output_file, 'w', encoding='utf-8') as fout:
        for item in modified_data:
            fout.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"修改后的 JSON 文件已保存到 {output_file}")

if __name__ == "__main__":
    # 示例使用
    input_file_path = './LearningMode/p7/p7.json'  # 输入文件路径
    output_file_path = './LearningMode/p7/p7_output.json'  # 输出文件路径
    prefix_string = 'p7_'  # 您想要添加的前缀

    modify_json(input_file_path, output_file_path, prefix_string)
