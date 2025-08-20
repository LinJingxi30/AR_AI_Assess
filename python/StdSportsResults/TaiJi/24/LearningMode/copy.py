import json

def process_json(input_file, output_file):
    """
    读取指定路径的JSON文件，将每一行JSON重复一次并保存到新的文件中。

    :param input_file: 输入的JSON文件路径
    :param output_file: 输出的JSON文件路径
    """
    final_data = []  # 用于存储处理后的所有JSON数据

    # 逐行读取输入文件
    with open(input_file, 'r', encoding='utf-8') as infile:
        for line in infile:
            if line.strip():  # 排除空行
                try:
                    # 解析每一行的 JSON 数据
                    json_data = json.loads(line.strip())
                    # 将解析后的数据添加两次到结果列表
                    final_data.append(json_data)
                    final_data.append(json_data)  # 复制一遍
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误，跳过此行：{line.strip()}")
                    continue

    # 将结果数据保存到输出文件中
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for item in final_data:
            json.dump(item, outfile, ensure_ascii=False)
            outfile.write('\n')  # 每个 JSON 数据写入一行

    print(f"处理完成，结果已保存到 {output_file}")


# 指定输入文件和输出文件路径
input_file = 'p4.json'  # 原始JSON文件路径
output_file = 'p4_slow.json'  # 处理后的JSON文件路径

# 调用函数处理文件
process_json(input_file, output_file)