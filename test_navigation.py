#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光遇辅助程序导航模块测试
"""

import cv2
from core.navigator import Navigator


# 初始化导航器
nav = Navigator("dataset/isle_dawn", "dataset/isle_dawn/waypoints.json")

# 读取一张实际的图片（假设frame_0005.jpg为当前游戏画面）
current_screen = cv2.imread("dataset/isle_dawn/frame_0005.jpg")

if current_screen is None:
    print("无法读取测试图片，请检查文件路径！")
    exit(1)

# 计算偏移量和匹配分数
offset, score = nav.calculate_offset(current_screen)

print(f"偏移量: {offset:.2f} (正数向右，负数向左)")
print(f"匹配分: {score:.2f}")

# 检查是否到达目标
if nav.should_switch_target(score):
    print("到达目标！切换下一个！")
    nav.load_target(nav.current_idx + 1)

# 测试切换到下一个目标
print("\n测试切换到下一个目标...")
nav.load_target(1)

# 读取另一张图片进行测试
current_screen2 = cv2.imread("dataset/isle_dawn/frame_0060.jpg")
if current_screen2 is not None:
    offset2, score2 = nav.calculate_offset(current_screen2)
    print(f"偏移量: {offset2:.2f}")
    print(f"匹配分: {score2:.2f}")

print("\n导航模块测试完成！")