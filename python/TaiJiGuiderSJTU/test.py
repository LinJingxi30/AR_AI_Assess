import json
import sys

from main import FULL_PATHS

# infile = r"E:\Github\repositories\media_pipe\python\StdSportsResults\TaiJi\C79-V2_points.json"
# outfile = r"E:\Github\repositories\media_pipe\python\StdSportsResults\TaiJi\C79-V2.1_points.json"

# with open(infile, 'r') as fin, open(outfile, 'w') as fout:
#     for line in fin:
#         if not line.strip():
#             continue
#         data = json.loads(line)
#         pts = data.get("points", {})
#         for key, coord in pts.items():
#             if isinstance(coord, list) and len(coord) == 2:
#                 coord[0] *= 1.74  # 横坐标调整
#                 coord[1] *= 1.84  # 纵坐标调整
#         fout.write(json.dumps(data) + "\n")

# def user_jsons_combine(id=None):
#     jsons_paths = []
#     for posture in FULL_PATHS.values():
#         for move in posture.values():
#             json_path = move.get("标准 JSON 文件路径")
#             if json_path:
#                 jsons_paths.append(json_path)

#     # 组合成一个大的 JSON 文件


import json
from pathlib import Path
from main import FULL_PATHS

def user_jsons_combine(id, save_path):
    """
    遍历 FULL_PATHS 中所有 posture 和 move，
    组合各个 JSON 文件的数据为如下格式：
    
    {
      "description": "",
      "data": {
          "p1": {
              "m1": [ {...}, {...}, ... ],
              "m2": [ ... ],
              ...
          },
          "p2": { ... },
          ...
      }
    }
    
    将生成的 JSON 数据写入 save_path 目录下的 differences-<id>.json 文件中。
    """
    combined_data = {
        "description": "",
        "data": {}
    }
    # 定义 posture 映射，比如 POSTURE_1 -> p1, POSTURE_2 -> p2, POSTURE_3 -> p3
    posture_mapping = {
        "POSTURE_1": "p1",
        "POSTURE_2": "p2",
        "POSTURE_3": "p3",
        "POSTURE_4": "p4",
    }
    
    for posture_key, moves in FULL_PATHS.items():
        p_key = posture_mapping.get(posture_key, posture_key)
        combined_data["data"][p_key] = {}
        for move_key, move_info in moves.items():
            # 将 MOVE_1 转换为 m1
            m_key = move_key.lower().replace("move_", "m")
            json_path = move_info.get("标准 JSON 文件路径")
            records = []
            if json_path and Path(json_path).exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                record = json.loads(line)
                                records.append(record)
                            except Exception as e:
                                print(f"解析 {json_path} 行数据错误：", e)
            combined_data["data"][p_key][m_key] = records

    # 将合成的数据直接写入 save_path 下的 differences-<id>.json 文件
    output_file = Path(save_path) / f"differences-{id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)
    print(f"组合后的 JSON 已保存到 {output_file}", file=sys.stderr)

# user_jsons_combine("test666", r"E:\Github\repositories\media_pipe\python\StdSportsResults\TaiJi")