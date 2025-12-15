#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光遇辅助程序视频处理器
将连续视频流转化为离散导航路点数据库
"""

import cv2
import numpy as np
import os
import argparse
from skimage.metrics import structural_similarity as ssim


def resize_video(video_path, output_path, target_width=640, target_height=360):
    """
    将视频缩放到目标分辨率
    
    Args:
        video_path: 输入视频路径
        output_path: 输出视频路径
        target_width: 目标宽度
        target_height: 目标高度
        
    Returns:
        bool: 处理成功返回True，否则返回False
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频文件: {video_path}")
        return False
    
    # 获取原始视频信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 创建视频编写器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (target_width, target_height))
    
    print(f"正在调整视频分辨率: {video_path}")
    print(f"原始分辨率: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    print(f"目标分辨率: {target_width}x{target_height}")
    print(f"总帧数: {total_frames}, FPS: {fps}")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 调整分辨率
        resized_frame = cv2.resize(frame, (target_width, target_height))
        out.write(resized_frame)
        
        frame_count += 1
        if frame_count % 100 == 0:
            print(f"处理进度: {frame_count}/{total_frames} ({frame_count/total_frames:.1%})")
    
    cap.release()
    out.release()
    print(f"视频分辨率调整完成，输出文件: {output_path}")
    return True


def get_sky_mask(frame_width, frame_height):
    """
    创建遮罩，遮挡游戏UI和主角等干扰元素
    
    Args:
        frame_width: 帧宽度
        frame_height: 帧高度
        
    Returns:
        numpy.ndarray: 遮罩图像
    """
    # 创建一个全白图像 (255)
    mask = np.ones((frame_height, frame_width), dtype=np.uint8) * 255
    
    # 1. 遮挡主角 (中心偏下)
    c_x, c_y = frame_width // 2, frame_height // 2
    cv2.rectangle(mask, 
                  (c_x - int(frame_width * 0.15), c_y - int(frame_height * 0.1)),  # 左上
                  (c_x + int(frame_width * 0.15), frame_height),                # 右下(到底)
                  0, -1)  # 填黑
    
    # 2. 遮挡顶部能量槽 UI
    cv2.rectangle(mask, 
                  (c_x - int(frame_width * 0.2), 0),
                  (c_x + int(frame_width * 0.2), int(frame_height * 0.15)),
                  0, -1)

    # 3. 遮挡左下角聊天 UI
    cv2.rectangle(mask, (0, int(frame_height * 0.8)), (int(frame_width * 0.2), frame_height), 0, -1)
    
    # 4. 遮挡右上角设置按钮
    cv2.rectangle(mask, (int(frame_width * 0.9), 0), (frame_width, int(frame_height * 0.1)), 0, -1)
    
    # 5. 遮挡右下角魔法按钮
    cv2.rectangle(mask, (int(frame_width * 0.8), int(frame_height * 0.8)), (frame_width, frame_height), 0, -1)
    
    return mask


def extract_keyframes(video_path, output_folder, threshold=0.6, target_size=(640, 360)):
    """
    智能关键帧提取，根据画面变化自动提取关键帧
    
    Args:
        video_path: 输入视频路径
        output_folder: 输出文件夹
        threshold: 画面变化阈值 (0-1)，值越小提取越频繁
        target_size: 目标分辨率
        
    Returns:
        int: 提取的关键帧数量
    """
    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频文件: {video_path}")
        return 0
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 获取我们定义的遮罩
    mask = get_sky_mask(width, height)
    
    prev_frame_gray = None
    frame_count = 0
    saved_count = 0
    
    print(f"正在提取关键帧: {video_path}")
    print(f"视频信息: {width}x{height}, {fps} FPS")
    print(f"关键帧提取阈值: {threshold}")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 1. 转灰度 (降低计算量，且跑图主要靠轮廓)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 2. 应用遮罩 (只计算有效区域的差异)
        masked_gray = cv2.bitwise_and(gray, gray, mask=mask)
        
        should_save = False
        
        if prev_frame_gray is None:
            should_save = True
        else:
            # 3. 计算结构相似性指数 (SSIM)
            # SSIM值越接近1，表示图像越相似
            current_ssim = ssim(prev_frame_gray, masked_gray)
            
            # 如果画面变动超过一定阈值
            if current_ssim < (1 - threshold):
                should_save = True
        
        if should_save:
            # 保存关键帧
            filename = f"{output_folder}/frame_{saved_count:04d}.jpg"
            cv2.imwrite(filename, frame)  # 保存原彩图用于调试，运行时再转灰度
            
            # 处理第一帧的情况，current_ssim可能未定义
            ssim_info = f", SSIM: {current_ssim:.3f}" if 'current_ssim' in locals() else ""
            print(f"Saved keyframe {saved_count} at time {frame_count/fps:.2f}s{ssim_info}")
            
            prev_frame_gray = masked_gray
            saved_count += 1
            
        frame_count += 1
    
    cap.release()
    print(f"关键帧提取完成，共提取: {saved_count} 帧")
    return saved_count


def main():
    """
    主函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="光遇辅助程序视频处理器")
    parser.add_argument('--input', '-i', required=True, help='输入视频文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出关键帧文件夹路径')
    parser.add_argument('--threshold', '-t', type=float, default=0.6, help='关键帧提取阈值 (0-1)')
    parser.add_argument('--width', '-w', type=int, default=640, help='目标宽度')
    parser.add_argument('--height', '-H', type=int, default=360, help='目标高度')
    parser.add_argument('--resize_only', action='store_true', help='只调整视频分辨率，不提取关键帧')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # 生成调整分辨率后的视频路径
    base_name = os.path.splitext(os.path.basename(args.input))[0]
    resized_video_path = f"{args.output}/{base_name}_resized.mp4"
    
    # 1. 调整视频分辨率
    resize_success = resize_video(args.input, resized_video_path, args.width, args.height)
    if not resize_success:
        return
    
    # 2. 提取关键帧
    if not args.resize_only:
        extract_keyframes(resized_video_path, args.output, args.threshold)
    
    print("视频处理完成！")


if __name__ == "__main__":
    main()