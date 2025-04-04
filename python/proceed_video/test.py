from PIL import Image


def convert_person_to_grayscale(image_path, output_path):
    # 打开图片
    img = Image.open(image_path)

    # 确保图片是 RGBA 模式（包含透明通道）
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # 分离出 RGB 和 Alpha 通道
    r, g, b, a = img.split()

    # 将 RGB 通道转换为灰度
    gray = Image.merge('RGB', (r, g, b)).convert('L')

    # 将灰度图转换回三通道（RGB），以便与 Alpha 通道合并
    gray_rgb = Image.merge('RGB', (gray, gray, gray))

    # 分离灰度图的 RGB 通道
    gray_r, gray_g, gray_b = gray_rgb.split()

    # 合并灰度 RGB 和原始 Alpha 通道
    result = Image.merge('RGBA', (gray_r, gray_g, gray_b, a))

    # 保存结果
    result.save(output_path, 'PNG')


# 使用示例
input_image = 'input.png'  # 替换为你的输入图片路径
output_image = 'output.png'  # 输出图片路径
convert_person_to_grayscale(input_image, output_image)
