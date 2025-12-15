#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光遇辅助程序导航模块
实现实时匹配与导航功能
"""

import cv2
import numpy as np
import os
import json
import time


class Navigator:
    def __init__(self, dataset_path, waypoint_config_path):
        self.dataset_path = dataset_path
        # 初始化 ORB 特征检测器
        self.orb = cv2.ORB_create(nfeatures=500)
        # 特征匹配器 (使用汉明距离)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # 加载路点数据
        self.waypoints = self._load_waypoints(waypoint_config_path)
        self.current_idx = 0
        
        # 预加载第一个目标图片
        self.current_target_img = None
        self.current_kp = None
        self.current_des = None
        self.load_target(0)

    def _load_waypoints(self, path):
        """加载 JSON 配置文件"""
        if not os.path.exists(path):
            print("警告：未找到路点配置文件，请先标注数据！")
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_target(self, idx):
        """切换到下一个目标路点"""
        if idx >= len(self.waypoints):
            print("已到达终点！")
            return False
            
        self.current_idx = idx
        wp = self.waypoints[idx]
        img_path = os.path.join(self.dataset_path, wp['img_name'])
        
        # 读取图片并提取特征
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        # 这里应该应用和提取时一样的 Mask，保证特征点不出现在UI或角色身上
        # (简化起见，这里假设提取的图片已经是处理过的或者是干净的)
        
        self.current_target_img = img
        self.current_kp, self.current_des = self.orb.detectAndCompute(img, None)
        print(f"切换目标 -> ID: {wp['id']} ({wp.get('description', '')})")
        return True

    def calculate_offset(self, screen_frame):
        """
        计算当前屏幕与目标图片的偏差
        返回: (x_offset, match_score)
        x_offset > 0: 目标在右边，需要右转
        x_offset < 0: 目标在左边，需要左转
        match_score: 匹配度 (0-1)，越高越好
        """
        if self.current_des is None:
            return 0, 0

        # 1. 处理当前屏幕帧
        gray = cv2.cvtColor(screen_frame, cv2.COLOR_BGR2GRAY)
        kp_screen, des_screen = self.orb.detectAndCompute(gray, None)
        
        if des_screen is None or len(des_screen) < 10:
            return 0, 0 # 画面太黑或无特征

        # 2. 特征匹配
        matches = self.matcher.match(self.current_des, des_screen)
        # 按距离排序，取最好的前N个匹配
        matches = sorted(matches, key=lambda x: x.distance)
        good_matches = matches[:20]
        
        if len(good_matches) < 5:
            return 0, 0 # 匹配失败

        # 3. 计算位置偏差
        # 获取匹配点在两张图中的坐标
        src_pts = np.float32([self.current_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp_screen[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        # 计算 X 轴的平均偏移量
        # dst_pts (屏幕) - src_pts (目标)
        # 如果 dst_pts 的 X 比 src_pts 小，说明目标在屏幕左边（屏幕画面偏右了）
        # 这是一个简化算法，更高级的是用 findHomography 计算透视变换
        diff = dst_pts - src_pts
        x_offset = np.mean(diff[:, :, 0])
        
        # 简单的评分机制：距离越小分越高
        avg_dist = np.mean([m.distance for m in good_matches])
        score = max(0, 1 - avg_dist / 100.0)

        # 可视化调试 (画出连线)
        # debug_img = cv2.drawMatches(self.current_target_img, self.current_kp, gray, kp_screen, good_matches, None)
        # cv2.imshow("Matching", debug_img)
        
        return -x_offset, score # 取反，使得正数代表"目标在右边"

    def should_switch_target(self, score):
        """判断是否已经到达当前目标"""
        # 如果匹配度极高，或者特征点偏移量非常小，说明到了
        # 这里的阈值需要调试
        return score > 0.85