import json
import sys
from pathlib import Path

def split_json_by_skip(input_file, output_dir):
    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    current_records = []
    file_count = 1

    # 逐行读取输入 JSON 文件
    with open(input_file, 'r', encoding='utf-8') as fin:
        for line in fin:
            line = line.strip()
            if not line:  # 忽略空行
                continue
            try:
                record = json.loads(line)

                # 将当前记录添加到列表
                current_records.append(record)

                # 检查 skip 字段
                if not record["points"].get("skip", True):
                    # 当 skip 为 false 时，保存当前记录到文件
                    if current_records:
                        output_file = Path(output_dir) / f"p9m{file_count}.json"
                        with open(output_file, 'w', encoding='utf-8') as fout:
                            for rec in current_records:
                                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        print(f"记录已保存到: {output_file}")
                        current_records.clear()  # 清空当前记录列表
                        file_count += 1  # 增加文件计数

            except json.JSONDecodeError as e:
                print(f"解析 JSON 时出现错误: {e}", file=sys.stderr)

    # 处理最后一组记录（如果有）
    if current_records:
        output_file = Path(output_dir) / f"records_{file_count}.json"
        with open(output_file, 'w', encoding='utf-8') as fout:
            for rec in current_records:
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"记录已保存到: {output_file}")

def main():


    split_json_by_skip(r"p9m1.json", r"p9")

if __name__ == "__main__":
    main()
