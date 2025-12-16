#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光遇辅助程序 - 核心输入模块
实现窗口焦点控制和启动自检程序
"""

import pydirectinput
import time
import random
import pygetwindow as gw
import win32gui
import win32con


class InputManager:
    def __init__(self, window_title="Sky"):
        # 极低延迟，防止操作卡顿
        pydirectinput.PAUSE = 0.005  
        self.window_title = window_title
        
    def focus_game_window(self):
        """
        强制激活游戏窗口，确保输入有效
        """
        try:
            windows = gw.getWindowsWithTitle(self.window_title)
            if windows:
                win = windows[0]
                # 如果窗口最小化了，还原它
                if win.isMinimized:
                    win.restore()
                # 强制置顶
                win.activate()
                # 备用方案：使用 win32gui 强制前台
                hwnd = win32gui.FindWindow(None, self.window_title)
                if hwnd:
                    win32gui.SetForegroundWindow(hwnd)
                return True
        except Exception as e:
            print(f"尝试激活窗口失败 (可能需要管理员权限): {e}")
        return False

    def run_startup_test(self):
        """
        启动自检程序：
        1. 旋转视角 (模拟鼠标移动)
        2. 前后左右移动 (测试键盘)
        """
        print(">>> 开始控制权自检程序 <<<")
        
        # 1. 确保游戏在最前端
        if not self.focus_game_window():
            print("错误：找不到游戏窗口或无法激活，测试中止！")
            return

        time.sleep(1) # 等待窗口切换完成

        # 2. 测试视角旋转 (模拟鼠标向右持续移动)
        print("测试：旋转视角 (360度)...")
        # 在3D游戏中，鼠标通常被锁定在中心，需要多次相对移动
        for _ in range(50):
            # X轴移动 30 像素 (向右)，Y轴 0
            pydirectinput.moveRel(30, 0, relative=True)
            time.sleep(0.02)
        
        time.sleep(0.5)

        # 3. 测试移动 (WASD)
        moves = [
            ('w', "向前"),
            ('s', "向后"),
            ('a', "向左"),
            ('d', "向右")
        ]

        for key, action in moves:
            print(f"测试：{action}移动 (3秒)...")
            pydirectinput.keyDown(key)
            time.sleep(3)
            pydirectinput.keyUp(key)
            time.sleep(0.5) # 缓冲

        print(">>> 自检完成 <<<")

    def random_sleep(self, base_time, variance=0.1):
        """
        随机睡眠，增加行为的自然性
        """
        actual_time = random.gauss(base_time, base_time * variance)
        if actual_time < 0: actual_time = 0
        time.sleep(actual_time)

    def move_mouse_smooth(self, x_offset, y_offset):
        """
        平滑移动鼠标，避免抖动
        """
        # 简单的分步移动
        steps = 5
        for _ in range(steps):
            pydirectinput.moveRel(int(x_offset/steps), int(y_offset/steps), relative=True)
            time.sleep(0.005)
