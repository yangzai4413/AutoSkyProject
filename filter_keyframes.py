#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键帧过滤脚本
每隔5张图片保留1张，减少关键帧数量
"""

import os
import argparse


def filter_keyframes(input_dir, step=5):
    """
    过滤关键帧，每隔step张保留1张
    
    Args:
        input_dir: 输入目录
        step: 保留间隔，每隔step张保留1张
    """
    # 获取所有关键帧图片
    files = [f for f in os.listdir(input_dir) if f.startswith('frame_') and f.endswith('.jpg')]
    
    # 按文件名排序
    files.sort()
    
    print(f"找到 {len(files)} 张关键帧图片")
    print(f"保留间隔: 每隔 {step} 张保留1张")
    
    # 计算需要保留的图片
    kept_files = []
    deleted_files = []
    
    for i, file in enumerate(files):
        if i % step == 0:
            kept_files.append(file)
        else:
            deleted_files.append(file)
    
    print(f"保留 {len(kept_files)} 张，删除 {len(deleted_files)} 张")
    
    # 执行删除操作
    for file in deleted_files:
        file_path = os.path.join(input_dir, file)
        os.remove(file_path)
    
    print(f"关键帧过滤完成！")
    print(f"保留的前10张图片: {kept_files[:10]}")
    print(f"删除的前10张图片: {deleted_files[:10]}")
    
    return len(kept_files), len(deleted_files)


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="关键帧过滤脚本")
    parser.add_argument('--input', '-i', required=True, help='输入关键帧目录')
    parser.add_argument('--step', '-s', type=int, default=5, help='保留间隔，每隔step张保留1张')
    
    args = parser.parse_args()
    
    # 检查输入目录是否存在
    if not os.path.exists(args.input):
        print(f"输入目录不存在: {args.input}")
        return
    
    # 执行过滤
    kept, deleted = filter_keyframes(args.input, args.step)
    
    print(f"\n过滤结果:")
    print(f"总图片数: {kept + deleted}")
    print(f"保留图片数: {kept}")
    print(f"删除图片数: {deleted}")
    print(f"保留比例: {kept / (kept + deleted):.2%}")


if __name__ == "__main__":
    main()