import cv2
import os
from pathlib import Path


def convert_to_grayscale(input_folder, output_folder):
    """
    将指定文件夹中的彩色照片转换为灰度照片，并保存到输出文件夹
    """
    # 确保输出文件夹存在
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # 支持的图片格式
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp')

    # 获取输入文件夹中的所有图片文件
    image_files = [f for f in os.listdir(input_folder)
                   if f.lower().endswith(supported_formats)]

    if not image_files:
        print(f"输入文件夹 {input_folder} 中没有找到支持的图片文件！")
        return

    # 处理每张图片
    for image_file in image_files:
        # 构造输入和输出路径
        input_path = os.path.join(input_folder, image_file)
        output_path = os.path.join(output_folder, f"gray_{image_file}")

        # 读取彩色图片
        img = cv2.imread(input_path)
        if img is None:
            print(f"无法读取图片: {input_path}")
            continue

        # 转换为灰度图
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 保存灰度图片
        cv2.imwrite(output_path, gray_img)
        print(f"已转换并保存: {output_path}")


def main():
    # 设置输入和输出文件夹路径
    input_folder = r"out_xuni_person_transparent"  # 替换为你的彩色图片文件夹路径
    output_folder = r"out_xuni_person_gray"  # 替换为你的输出文件夹路径

    # 检查输入文件夹是否存在
    if not os.path.exists(input_folder):
        # print(f"输入文件夹 {input_folder} 不存在！")
        return

    # 执行转换
    convert_to_grayscale(input_folder, output_folder)
    print("所有图片转换完成！")


if __name__ == "__main__":
    main()
