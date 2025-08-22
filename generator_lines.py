#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光谱分布图PNG生成器 - 无头服务器版本
专门用于Linux无头服务器环境，避免中文字体问题
"""

import json
import matplotlib

# 设置matplotlib后端为Agg（无头模式）
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import warnings

# 忽略所有matplotlib警告
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)


def read_spectrum_data(filename):
    """读取光谱数据文件"""
    spectrum_data = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:  # 跳过空行
                    data = json.loads(line)
                    spectrum_data.append(data)
        #print(f"✅ Successfully read {len(spectrum_data)} rows of data")
        return spectrum_data
    except FileNotFoundError:
        print(f"❌ Error: File not found {filename}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error: JSON format error - {e}")
        return []
    except Exception as e:
        print(f"❌ Error: Error reading file - {e}")
        return []


def get_next_filename(base_dir="model_runs_results/generat_word", base_name="line"):
    """获取下一个可用的文件名"""
    # 确保目录存在
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        #print(f"📁 Created directory: {base_dir}")

    # 查找下一个可用的文件名
    counter = 1
    while True:
        filename = os.path.join(base_dir, f"{base_name}{counter}.png")
        if not os.path.exists(filename):
            return filename
        counter += 1


def create_spectrum_png(spectrum_data, output_filename):
    """创建光谱分布图PNG"""
    if not spectrum_data:
        print("❌ No data to plot")
        return False

    # 设置matplotlib参数，避免字体问题
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.unicode_minus'] = False

    # 设置图片大小和DPI - 增加宽度以适应更多数据点
    plt.figure(figsize=(16, 8), dpi=300)

    # 获取波段名称（包含所有波段）
    bands = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'Clear1', 'NIR1', 'Clear2', 'NIR2']

    # 定义颜色和线型
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    line_styles = ['-', '--', '-.', ':']
    markers = ['o', 's', '^', 'D']

    # 计算所有数据的最大值和最小值，用于设置Y轴范围
    all_values = []
    for line_data in spectrum_data:
        line_values = list(line_data.values())[0]
        for band in bands:
            if band in line_values:
                all_values.append(line_values[band])

    min_value = min(all_values) if all_values else 0
    max_value = max(all_values) if all_values else 65535

    # 设置Y轴范围，留出一些边距
    y_margin = (max_value - min_value) * 0.1
    y_min = max(0, min_value - y_margin)
    y_max = min(65535, max_value + y_margin)

    # 绘制四条曲线
    for i, line_data in enumerate(spectrum_data):
        if i >= 4:  # 只绘制前4条曲线
            break

        line_key = list(line_data.keys())[0]
        line_values = list(line_data.values())[0]

        # 提取数据
        x_data = list(range(len(bands)))
        y_data = [line_values[band] for band in bands if band in line_values]

        # 绘制曲线
        plt.plot(x_data, y_data,
                 color=colors[i],
                 linestyle=line_styles[i],
                 marker=markers[i],
                 linewidth=2,
                 markersize=8,
                 label=f'Curve {line_key}')

        # 在每个点上标记数值
        for j, (x, y) in enumerate(zip(x_data, y_data)):
            plt.annotate(f'{y}',
                         xy=(x, y),
                         xytext=(0, 10),
                         textcoords='offset points',
                         ha='center',
                         va='bottom',
                         fontsize=8,
                         fontweight='bold',
                         color=colors[i])

    # 设置图表属性 - 使用英文标题
    plt.title('Spectrum Distribution Chart', fontsize=20, fontweight='bold', pad=20)
    plt.xlabel('Band', fontsize=14, fontweight='bold')
    plt.ylabel('Value', fontsize=14, fontweight='bold')

    # 设置X轴
    plt.xticks(range(len(bands)), bands, fontsize=12)
    plt.xlim(-0.5, len(bands) - 0.5)

    # 设置Y轴 - 精细刻度
    plt.ylim(y_min, y_max)

    # 计算合适的Y轴刻度间隔
    y_range = y_max - y_min
    if y_range <= 1000:
        step = 100
    elif y_range <= 5000:
        step = 500
    elif y_range <= 10000:
        step = 1000
    elif y_range <= 50000:
        step = 5000
    else:
        step = 10000

    # 生成Y轴刻度
    y_ticks = np.arange(int(y_min // step) * step, y_max + step, step)
    plt.yticks(y_ticks, [f'{int(tick)}' for tick in y_ticks], fontsize=10)

    # 添加网格
    plt.grid(True, alpha=0.3, linestyle='--')

    # 设置图例
    plt.legend(loc='upper right', fontsize=12, frameon=True, fancybox=True, shadow=True)

    # 调整布局
    plt.tight_layout()

    # 保存图片
    plt.savefig(output_filename, dpi=300, bbox_inches='tight', facecolor='white')
    #print(f"✅ Image saved to: {output_filename}")

    # 关闭图形，释放内存
    plt.close()

    return True


def sp_main(spectrum_file_path):
    """
    主函数

    Args:
        spectrum_file_path (str): 光谱数据文件路径，例如 'specturm.txt'
    """
    #print("🖼️ Spectrum PNG Generator (Headless) Starting...")
    #print("-" * 50)
    #print(f"📂 Input file: {spectrum_file_path}")

    # 读取数据
    spectrum_data = read_spectrum_data(spectrum_file_path)

    if not spectrum_data:
        print("❌ No data read, program exiting")
        return False

    # 获取下一个可用的文件名
    output_filename = get_next_filename()
    #print(f"📁 Output file: {output_filename}")

    # 生成PNG图片
    success = create_spectrum_png(spectrum_data, output_filename)

    if success:
        #print("\n🎉 Generation completed!")
        #print(f"📁 Generated file: {output_filename}")
        return output_filename
    else:
        print("\n❌ Generation failed!")
        return False


if __name__ == "__main__":
    # 默认使用 specturm.txt 文件
    txt = "upload_images/1754984861/specturm.txt"
    specturm_lines_output_image_path=sp_main(txt)
    print(specturm_lines_output_image_path)