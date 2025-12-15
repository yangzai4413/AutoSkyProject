#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光遇辅助程序UI控制器
实现紧急停止功能和状态显示
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import keyboard  # 需要 pip install keyboard 用于全局热键
from core.navigator import SkyNavigator
from core.input_controller import InputController
from main import screen_capture


class AutoSkyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoSky Controller")
        self.root.geometry("300x150")
        self.root.attributes('-topmost', True) # 窗口置顶

        # 状态变量
        self.is_running = False
        self.stop_event = threading.Event()
        self.thread = None

        # UI 组件
        self.status_label = ttk.Label(root, text="状态: 就绪", font=("Arial", 12))
        self.status_label.pack(pady=10)

        self.btn_frame = ttk.Frame(root)
        self.btn_frame.pack(pady=10)

        self.start_btn = ttk.Button(self.btn_frame, text="开始运行 (F9)", command=self.start_program)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(self.btn_frame, text="停止 (F10)", command=self.stop_program, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.info_label = ttk.Label(root, text="长按 F10 强制停止", foreground="red")
        self.info_label.pack(side=tk.BOTTOM, pady=5)

        # 注册全局热键
        keyboard.add_hotkey('f9', self.start_program)
        keyboard.add_hotkey('f10', self.stop_program)

    def start_program(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.status_label.config(text="状态: 运行中...", foreground="green")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        # 在新线程中运行主逻辑
        self.thread = threading.Thread(target=self._run_logic)
        self.thread.daemon = True
        self.thread.start()

    def stop_program(self):
        if not self.is_running:
            return

        self.status_label.config(text="状态: 正在停止...", foreground="orange")
        self.stop_event.set() # 发送停止信号
        
        # 等待线程结束（非阻塞方式）
        self.root.after(100, self._check_thread_stop)

    def _check_thread_stop(self):
        if self.thread and self.thread.is_alive():
            self.root.after(100, self._check_thread_stop)
        else:
            self.is_running = False
            self.status_label.config(text="状态: 已停止", foreground="black")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    def _run_logic(self):
        """
        运行主逻辑
        """
        print("导航线程启动")
        
        try:
            # 初始化导航器和输入控制器
            nav = SkyNavigator("dataset/isle_dawn", "dataset/isle_dawn/waypoints.json")
            ctrl = InputController()
            
            # 初始状态
            is_moving = False
            
            print("开始初始校准...")
            # 运行初始校准
            calibrated = self._initial_calibration(nav, ctrl)
            
            if not calibrated:
                print("校准失败，停止运行")
                return
            
            print("校准成功，开始导航")
            
            while not self.stop_event.is_set():
                # 1. 屏幕截图
                frame = screen_capture()
                
                # 2. 计算偏移量
                offset_x, similarity = nav.calculate_offset(frame)
                
                # 3. 检查是否到达目标
                if nav.check_arrival(similarity):
                    print(f"到达目标 ID: {nav.current_idx}")
                    # 执行路点定义的特殊动作
                    current_action = nav.get_current_action()
                    action = current_action.get('action', 'walk')
                    
                    if action == 'fly_start':
                        print("执行起飞动作")
                        ctrl.jump()
                        time.sleep(0.5)
                        ctrl.fly_toggle()
                        time.sleep(1) # 等待起飞动画
                    elif action == 'interact':
                        print("执行交互动作")
                        ctrl.interact()
                        time.sleep(1) # 等待交互完成
                    elif action == 'jump':
                        print("执行跳跃动作")
                        ctrl.jump()
                        time.sleep(0.5)
                    
                    # 切换下一个目标
                    nav.next_waypoint()
                    continue
                
                # 4. 自动视角调整
                if not nav.is_blind():
                    ctrl.align_camera(offset_x)
                
                # 5. 保持前进
                if not is_moving:
                    is_moving = True
                    ctrl.move_forward()
                
                # 6. 限制帧率
                time.sleep(0.1)
                
        except Exception as e:
            print(f"运行出错: {e}")
        finally:
            # 确保异常退出时UI状态重置
            print("清理资源...")
            ctrl.stop_all_movement()
            self.stop_program()
    
    def _initial_calibration(self, nav, ctrl):
        """
        初始校准：寻找匹配的环境
        
        Args:
            nav: SkyNavigator 实例
            ctrl: InputController 实例
            
        Returns:
            bool: 校准成功返回 True，否则返回 False
        """
        search_attempts = 0
        
        while not self.stop_event.is_set():
            # 1. 看一眼
            frame = screen_capture()
            offset, score = nav.calculate_offset(frame)
            
            # 2. 判断
            if score > 0.6: # 找到了高置信度的匹配
                print(f"校准成功！当前匹配分: {score:.2f}")
                # 进行微调，把视角对正
                if abs(offset) > 10:
                    ctrl.align_camera(offset)
                    time.sleep(0.5)
                    continue
                return True # 进入正式导航
                
            # 3. 没找到，尝试原地旋转寻找
            print(f"未找到目标 (Score: {score:.2f})，正在搜索环境...")
            # 向右转一点
            ctrl.align_camera(30)
            time.sleep(0.5) # 等画面稳定
            
            search_attempts += 1
            if search_attempts > 12: # 转了一圈也没找到
                print("校准失败：请手动移动角色到近似起始位置")
                return False


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoSkyGUI(root)
    root.mainloop()