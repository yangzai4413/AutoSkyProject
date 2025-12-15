#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光遇辅助程序导航模块
实现基于ORB特征的实时匹配算法
"""

import cv2
import numpy as np
import os
import json
import time


class SkyNavigator:
    def __init__(self, dataset_path, waypoints_file):
        self.dataset_path = dataset_path
        self.waypoints = self._load_json(waypoints_file)
        self.current_idx = 0
        
        # 初始化 ORB 特征提取器
        # nfeatures=500: 限制特征点数量，保证速度
        self.orb = cv2.ORB_create(nfeatures=500)
        
        # 初始化匹配器 (使用汉明距离，适合二进制描述符)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # 缓存当前目标的数据，避免每帧重复读取硬盘
        self.target_img = None
        self.target_kp = None
        self.target_des = None
        
        # 加载第一个目标
        self.load_waypoint(0)

    def _load_json(self, path):
        """加载 JSON 配置文件"""
        if not os.path.exists(path):
            print(f"警告：未找到路点配置文件 -> {path}")
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_waypoint(self, index):
        """加载指定索引的路点作为当前目标"""
        if index >= len(self.waypoints):
            print("导航结束：已到达终点")
            return False
            
        self.current_idx = index
        wp = self.waypoints[index]
        img_path = os.path.join(self.dataset_path, wp['img_name'])
        
        if not os.path.exists(img_path):
            print(f"错误：找不到图片 {img_path}")
            return False

        # 读取并预处理目标图片
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        self.target_img = img
        # 提取目标的特征点和描述符
        self.target_kp, self.target_des = self.orb.detectAndCompute(img, None)
        
        print(f"切换目标 -> ID: {wp['id']} Action: {wp['action']} {wp.get('description', '')}")
        return True

    def get_current_action(self):
        """获取当前路点的动作类型"""
        if self.current_idx < len(self.waypoints):
            return self.waypoints[self.current_idx]
        return None

    def calculate_offset(self, screen_frame):
        """
        核心算法：计算当前屏幕画面相对于目标画面的偏差
        Returns:
            offset_x: 水平偏差 (负数偏左，正数偏右)
            similarity: 匹配相似度 (0.0 - 1.0)
        """
        if self.target_des is None:
            return 0, 0

        # 1. 预处理屏幕画面
        gray_screen = cv2.cvtColor(screen_frame, cv2.COLOR_BGR2GRAY)
        
        # 2. 提取屏幕特征
        screen_kp, screen_des = self.orb.detectAndCompute(gray_screen, None)
        
        if screen_des is None or len(screen_des) < 10:
            # 画面太黑或无纹理（如纯色云层），无法匹配
            return 0, 0.0

        # 3. 特征匹配
        matches = self.matcher.match(self.target_des, screen_des)
        
        # 4. 筛选优质匹配点 (排序)
        matches = sorted(matches, key=lambda x: x.distance)
        
        # 取前15%的匹配点，或者至少前10个
        num_good = max(10, int(len(matches) * 0.15))
        good_matches = matches[:num_good]
        
        if len(good_matches) < 5:
            return 0, 0.0

        # 5. 计算平均位置偏差
        # queryIdx -> target image (目标图)
        # trainIdx -> screen image (当前屏幕)
        
        src_pts = np.float32([self.target_kp[m.queryIdx].pt for m in good_matches])
        dst_pts = np.float32([screen_kp[m.trainIdx].pt for m in good_matches])
        
        # 计算重心 (Centroid) 的差异
        # 如果 dst_center_x > src_center_x，说明屏幕里的物体在右边 -> 或者是视角偏左了？
        # 在FPS/TPS游戏中：
        # 如果目标物体在屏幕右侧 (dst_x 大)，我们需要向右转鼠标，把它移到中心？
        # 不，我们希望屏幕画面(dst) 变成 目标画面(src)。
        # 如果 dst_x (当前) > src_x (目标)，说明物体偏右，我们需要向右转视角来对准它。
        
        center_src = np.mean(src_pts, axis=0)
        center_dst = np.mean(dst_pts, axis=0)
        
        offset_x = center_dst[0] - center_src[0]
        
        # 6. 计算相似度评分 (基于特征点距离的倒数)
        avg_dist = np.mean([m.distance for m in good_matches])
        # 距离越小越相似。通常 avg_dist 在 30-70 之间。
        # 归一化一个分数
        similarity = max(0, 1 - (avg_dist / 100.0))
        
        return offset_x, similarity

    def check_arrival(self, similarity):
        """判断是否到达当前路点"""
        # 如果匹配度超过路点设定的阈值
        threshold = self.waypoints[self.current_idx].get('match_threshold', 0.6)
        if similarity > threshold:
            return True
        return False

    def next_waypoint(self):
        """切换到下一个路点"""
        return self.load_waypoint(self.current_idx + 1)