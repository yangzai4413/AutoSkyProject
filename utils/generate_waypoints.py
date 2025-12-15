#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光遇辅助程序路点配置生成脚本
根据图片文件夹自动生成路点配置文件
"""

import os
import json
import argparse


def generate_json(dataset_folder, output_file):
    """
    生成路点配置文件
    
    Args:
        dataset_folder: 图片数据集文件夹路径
        output_file: 输出JSON文件路径
    """
    # 获取所有图片文件
    files = sorted([f for f in os.listdir(dataset_folder) 
                  if f.endswith('.jpg') or f.endswith('.png')])
    
    waypoints = []
    for i, filename in enumerate(files):
        # 默认动作都是 "walk" (行走/滑行)
        # 默认指令是 "align" (对准目标)
        wp = {
            "id": i,
            "img_name": filename,
            "action": "walk",      # 默认动作
            "duration": 0,         # 持续时间(仅对盲操作有效)
            "match_threshold": 0.6 # 到达判定的匹配度阈值
        }
        
        # 简单的启发式逻辑：如果是第一张，标记为起点
        if i == 0:
            wp["description"] = "Start Point"
            
        waypoints.append(wp)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(waypoints, f, indent=2, ensure_ascii=False)
    
    print(f"成功生成路点文件: {output_file}，共包含 {len(waypoints)} 个节点。")
    print("请务必手动检查并修改特殊节点（如起飞、跳跃点）！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="光遇辅助程序路点配置生成脚本")
    parser.add_argument('--input', '-i', required=True, 
                      help='图片数据集文件夹路径')
    parser.add_argument('--output', '-o', 
                      help='输出JSON文件路径，默认在数据集文件夹下生成waypoints.json')
    
    args = parser.parse_args()
    
    # 检查输入目录是否存在
    if not os.path.exists(args.input):
        print(f"错误：目录不存在 -> {args.input}")
        exit(1)
    
    # 确定输出文件路径
    if args.output:
        output_path = args.output
    else:
        output_path = os.path.join(args.input, "waypoints.json")
    
    # 执行生成
    generate_json(args.input, output_path)