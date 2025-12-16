#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光遇辅助程序 - 视觉处理模块
实现区域截屏和图像预处理
"""

import cv2
import numpy as np
import pyautogui
import pygetwindow as gw


class VisionSystem:
    def __init__(self, window_title="Sky"):
        self.window_title = window_title
        self.game_region = None # 缓存窗口位置 (x, y, w, h)

    def update_window_region(self):
        """
        查找游戏窗口的位置
        """
        try:
            windows = gw.getWindowsWithTitle(self.window_title)
            if windows:
                win = windows[0]
                # 获取窗口的客户区坐标
                self.game_region = (win.left, win.top, win.width, win.height)
                return True
        except Exception:
            pass
        return False

    def capture_screen(self):
        """
        只截取游戏窗口区域，忽略外部干扰
        """
        # 每次截图前检查一下窗口位置（防止玩家拖动窗口）
        if not self.update_window_region():
            print("警告：未找到游戏窗口，全屏截图")
            screenshot = pyautogui.screenshot() # 降级为全屏
        else:
            # region=(left, top, width, height)
            screenshot = pyautogui.screenshot(region=self.game_region)

        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    def _preprocess(self, img):
        """
        图像预处理，使用修正后的低阈值Canny边缘检测
        """
        if img is None:
            return None
            
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # 使用修正后的低阈值，添加L2gradient=True提高边缘检测质量
        edges = cv2.Canny(gray, 20, 60, L2gradient=True)
        return edges

    def show_debug_view(self, img, window_name="Bot View"):
        """
        显示调试视图，缩放为固定大小
        """
        resized = cv2.resize(img, (640, 360))
        cv2.imshow(window_name, resized)
