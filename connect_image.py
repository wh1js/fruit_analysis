import os
import re
from typing import List
from PIL import Image






def connect_images(left_two_paths: List[str], right_two_paths: List[str]) -> str:
    """
    接收两个列表（各含2个图像路径）：
    - left_two_paths: 前两个图像，纵向排布在左侧
    - right_two_paths: 后两个图像，纵向排布在右侧

    将四张图拼接为两列图（左右各两张纵向）并保存到
    model_runs_results/connected_images/connected_{n}.png（n逐次+1）

    返回：最终保存的文件路径
    """
    if len(left_two_paths) != 2 or len(right_two_paths) != 2:
        raise ValueError("每个列表必须恰好包含2个图像路径")

    # 打开并统一为RGB
    left_images = [Image.open(p).convert("RGB") for p in left_two_paths]
    right_images = [Image.open(p).convert("RGB") for p in right_two_paths]

    # 计算左右列尺寸
    left_col_width = max(img.width for img in left_images)
    left_col_height = sum(img.height for img in left_images)

    right_col_width = max(img.width for img in right_images)
    right_col_height = sum(img.height for img in right_images)

    final_width = left_col_width + right_col_width
    final_height = max(left_col_height, right_col_height)

    # 创建画布（白底）
    canvas = Image.new("RGB", (final_width, final_height), color=(255, 255, 255))

    # 粘贴左列（顶对齐）
    y_offset = 0
    for img in left_images:
        canvas.paste(img, (0, y_offset))
        y_offset += img.height

    # 粘贴右列（顶对齐）
    y_offset = 0
    for img in right_images:
        canvas.paste(img, (left_col_width, y_offset))
        y_offset += img.height

    # 生成输出路径并保存
    out_dir = os.path.join("model_runs_results", "connected_images")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    max_idx = 0
    pattern = re.compile(r"^connected_(\d+)\.png$")
    for name in os.listdir(out_dir):
        match = pattern.match(name)
        if match:
            try:
                idx = int(match.group(1))
                if idx > max_idx:
                    max_idx = idx
            except ValueError:
                pass

    out_path = os.path.join(out_dir, f"connected_{max_idx + 1}.png")
    canvas.save(out_path, format="PNG")

    return out_path


