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
    def __init__(self, dataset_path, waypoints_file, use_edge_feature=True):
        self.dataset_path = dataset_path
        self.waypoints = self._load_json(waypoints_file)
        self.current_idx = 0
        self.use_edge_feature = use_edge_feature # 新增：是否启用边缘特征
        
        # 调整 ORB 参数：因为边缘图特征点较少，需要降低阈值灵敏度
        self.orb = cv2.ORB_create(nfeatures=1000, scoreType=cv2.ORB_FAST_SCORE)
        
        # 初始化匹配器 (使用汉明距离，适合二进制描述符)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # 缓存当前目标的数据，避免每帧重复读取硬盘
        self.target_img = None
        self.target_kp = None
        self.target_des = None
        
        # 加载第一个目标
        self.load_waypoint(0)
        
        # 状态追踪：用于盲飞模式
        self.consecutive_misses = 0 # 连续丢失目标的帧数
        self.blind_threshold = 10   # 连续10帧匹配不上，认为丢失视野

    def _load_json(self, path):
        """加载 JSON 配置文件"""
        if not os.path.exists(path):
            print(f"警告：未找到路点配置文件 -> {path}")
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _preprocess(self, img):
        """
        核心改进：图像预处理
        将图像转换为边缘图，抵抗光照变化
        """
        # 1. 统一转灰度
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        if self.use_edge_feature:
            # 2. Canny 边缘检测
            # 阈值需要根据晨岛的画风微调，建议 50, 150
            edges = cv2.Canny(gray, 50, 150)
            return edges
        else:
            return gray

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
        raw_img = cv2.imread(img_path)
        # 注意：这里要对目标图做同样的预处理（转边缘）
        processed_img = self._preprocess(raw_img)
        self.target_img = processed_img
        # 提取目标的特征点和描述符
        self.target_kp, self.target_des = self.orb.detectAndCompute(processed_img, None)
        
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

        # 1. 预处理屏幕画面 (转边缘)
        processed_screen = self._preprocess(screen_frame)
        
        # 2. 提取屏幕特征
        screen_kp, screen_des = self.orb.detectAndCompute(processed_screen, None)
        
        if screen_des is None or len(screen_des) < 5:
            # 画面太黑或无纹理（如纯色云层），无法匹配
            self.consecutive_misses += 1
            return 0, 0.0

        # 3. 特征匹配
        matches = self.matcher.match(self.target_des, screen_des)
        
        # 4. 筛选优质匹配点 (排序)
        matches = sorted(matches, key=lambda x: x.distance)
        
        # 取前 15% 且距离小于 60 的点（边缘匹配容错率要低一点）
        good_matches = [m for m in matches[:int(len(matches)*0.15)] if m.distance < 60]
        
        if len(good_matches) < 4:
            self.consecutive_misses += 1
            return 0, 0.0

        # 5. 计算平均位置偏差
        # queryIdx -> target image (目标图)
        # trainIdx -> screen image (当前屏幕)
        
        src_pts = np.float32([self.target_kp[m.queryIdx].pt for m in good_matches])
        dst_pts = np.float32([screen_kp[m.trainIdx].pt for m in good_matches])
        
        # 计算重心 (Centroid) 的差异
        center_src = np.mean(src_pts, axis=0)
        center_dst = np.mean(dst_pts, axis=0)
        
        offset_x = center_dst[0] - center_src[0]
        
        # 6. 重新计算分数逻辑，适应边缘特征
        avg_dist = np.mean([m.distance for m in good_matches])
        similarity = max(0, 1 - (avg_dist / 80.0)) # 调整分母以适应边缘特征
        
        # 更新连续丢失目标的帧数
        if similarity < 0.2: # 假设 0.2 是极低分
            self.consecutive_misses += 1
        else:
            self.consecutive_misses = 0
        
        return offset_x, similarity
        
    def is_blind(self):
        """
        判断是否进入盲飞模式
        Returns:
            bool: True 表示进入盲飞模式，False 表示正常导航模式
        """
        return self.consecutive_misses > self.blind_threshold

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