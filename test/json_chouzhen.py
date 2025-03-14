import json
import math

# 计算两个姿态之间的差异（欧氏距离）
def calculate_pose_difference(pose1, pose2):
    difference = 0
    for i in range(0, len(pose1), 3):  # 每3个值表示一个点的 (x, y, z)
        x1, y1, z1 = pose1[i], pose1[i + 1], pose1[i + 2]
        x2, y2, z2 = pose2[i], pose2[i + 1], pose2[i + 2]
        difference += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
    return difference

# 主函数
def main():
    # 读取 JSON 文件
    json_path = r"F:\task\media_pipe\savedjsons\part22.json"  # 替换为你的 JSON 文件路径
    output_json_path = r"D:\Desktop\output_poses22.json"  # 保存明显变化的 JSON 文件路径
    threshold = 900  # 设定动作变化的阈值

    with open(json_path, 'r') as f:
        lines = f.readlines()

    # 初始化变量
    prev_pose = None
    output_data = []

    # 逐行处理 JSON 数据
    for line in lines:
        data = json.loads(line.strip())
        current_pose = data["poses"]

        # 如果是第一行，直接保存
        if prev_pose is None:
            output_data.append(data)
        else:
            # 计算当前姿态与前一姿态的差异
            difference = calculate_pose_difference(prev_pose, current_pose)

            # 如果差异超过阈值，保存当前帧
            if difference > threshold:
                output_data.append(data)

        # 更新前一姿态
        prev_pose = current_pose

    # 将明显变化的帧保存到新的 JSON 文件
    with open(output_json_path, 'w') as f_out:
        for data in output_data:
            f_out.write(json.dumps(data) + "\n")

    print(f"已保存明显变化的帧到 {output_json_path}")

if __name__ == "__main__":
    main()
