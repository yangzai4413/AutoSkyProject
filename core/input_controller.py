#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光遇辅助程序输入控制器
封装底层键鼠操作，加入PID控制算法
"""

import pydirectinput
import time
import threading


class InputController:
    def __init__(self):
        pydirectinput.PAUSE = 0.001  # 降低库内部延迟
        self.screen_width = 1920     # 根据屏幕分辨率调整
        self.screen_height = 1080
        
        # PID 控制参数 (需要调试)
        # P (比例): 偏差越大，修正越快
        self.kp = 0.5
        # 死区: 偏差小于这个值时不移动，防止抖动
        self.deadzone = 15

    def align_camera(self, offset_x):
        """
        根据视觉偏差调整视角
        offset_x > 0: 目标在右，鼠标向右移
        offset_x < 0: 目标在左，鼠标向左移
        """
        if abs(offset_x) < self.deadzone:
            return

        # 简单的 P 控制器
        # 限制单次最大移动量，防止甩飞
        move_x = int(offset_x * self.kp)
        move_x = max(min(move_x, 50), -50)
        
        pydirectinput.moveRel(move_x, 0, relative=True)

    def move_forward(self, duration=None):
        """按住W前进"""
        if duration:
            pydirectinput.keyDown('w')
            time.sleep(duration)
            pydirectinput.keyUp('w')
        else:
            # 持续按住模式（需要在主循环外部管理状态）
            pydirectinput.keyDown('w')

    def stop_moving(self):
        """停止前进"""
        pydirectinput.keyUp('w')

    def jump(self):
        """跳跃"""
        pydirectinput.press('space')
        
    def fly_toggle(self):
        """切换飞行模式"""
        pydirectinput.press('space') # 根据键位配置调整
        
    def interact(self):
        """交互动作（点火、点蜡烛等）"""
        pydirectinput.press('e')
        
    def move_left(self):
        """按住A向左移动"""
        pydirectinput.keyDown('a')
        
    def move_right(self):
        """按住D向右移动"""
        pydirectinput.keyDown('d')
        
    def move_backward(self):
        """按住S向后移动"""
        pydirectinput.keyDown('s')
        
    def stop_all_movement(self):
        """停止所有移动"""
        pydirectinput.keyUp('w')
        pydirectinput.keyUp('a')
        pydirectinput.keyUp('s')
        pydirectinput.keyUp('d')