#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光遇辅助程序UI控制器 - 高级版
实现紧急停止功能和状态显示
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import keyboard  # 需要 pip install keyboard 用于全局热键
import queue
import os
from PIL import Image, ImageTk
from main import main_loop


class AdvancedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoSky Pro Dashboard")
        self.root.geometry("800x600")
        self.root.attributes('-topmost', True) # 窗口置顶
        
        # 数据通信队列 (Logic Thread -> UI Thread)
        self.data_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # === 布局 ===
        # 左侧：控制区
        left_panel = ttk.Frame(root, padding="10")
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(left_panel, text="控制台", font=16).pack(pady=10)
        self.btn_start = ttk.Button(left_panel, text="启动 (F9)", command=self.start)
        self.btn_start.pack(fill=tk.X, pady=5)
        self.btn_stop = ttk.Button(left_panel, text="停止 (F10)", command=self.stop, state=tk.DISABLED)
        self.btn_stop.pack(fill=tk.X, pady=5)
        
        # 实时数据区
        self.lbl_status = ttk.Label(left_panel, text="状态: 就绪", foreground="gray")
        self.lbl_status.pack(pady=20)
        
        self.var_score = tk.StringVar(value="匹配分: 0.00")
        self.var_thresh = tk.StringVar(value="阈值: 0.00")
        
        ttk.Label(left_panel, textvariable=self.var_score, font=("Arial", 12)).pack()
        ttk.Label(left_panel, textvariable=self.var_thresh, font=("Arial", 12)).pack()
        
        # 进度条 (可视化匹配分)
        self.score_bar = ttk.Progressbar(left_panel, length=150, mode='determinate', maximum=1.0)
        self.score_bar.pack(pady=5)
        
        # 右侧：视觉区
        right_panel = ttk.Frame(root, padding="10")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_panel, text="当前目标路点 (初始位置校对)", font=12).pack()
        
        # 图片显示容器
        self.img_label = ttk.Label(right_panel, text="等待加载...")
        self.img_label.pack(pady=10, expand=True)
        
        # 定时刷新 UI
        self.root.after(100, self.update_ui_from_queue)

        # 注册全局热键
        keyboard.add_hotkey('f9', self.start)
        keyboard.add_hotkey('f10', self.stop)

    def update_image(self, img_path):
        """更新 UI 显示的目标图片"""
        if not os.path.exists(img_path):
            return
            
        # 使用 Pillow 加载并调整大小
        pil_img = Image.open(img_path)
        # 保持比例缩放以适应 UI
        pil_img.thumbnail((480, 270))
        tk_img = ImageTk.PhotoImage(pil_img)
        
        self.img_label.configure(image=tk_img, text="")
        self.img_label.image = tk_img # 保持引用防止被垃圾回收

    def start(self):
        if self.btn_start['state'] == tk.DISABLED:
            return
        
        self.stop_event.clear()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.lbl_status.config(text="运行中...", foreground="green")
        
        # 启动逻辑线程
        t = threading.Thread(target=self.run_logic_thread)
        t.daemon = True
        t.start()

    def stop(self):
        if self.btn_stop['state'] == tk.DISABLED:
            return
        
        self.lbl_status.config(text="状态: 正在停止...", foreground="orange")
        self.stop_event.set() # 发送停止信号
        
        # 等待线程结束（非阻塞方式）
        self.root.after(100, self.check_thread_stop)

    def check_thread_stop(self):
        # 检查线程是否停止 - 这里简化处理，直接重置UI状态
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.lbl_status.config(text="已停止", foreground="black")

    def run_logic_thread(self):
        """
        这里运行原来的 main_loop
        """
        # 模拟传入回调函数给 main_loop
        # 这里的 callback 是用来实时汇报数据的
        def status_callback(current_img_path, score, threshold):
            self.data_queue.put({
                "type": "update",
                "img": current_img_path,
                "score": score,
                "thresh": threshold
            })
            
        try:
            # 调用修改后的 main_loop
            main_loop(self.stop_event, status_callback)
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.data_queue.put({"type": "stop"})

    def update_ui_from_queue(self):
        """在主线程中轮询队列，更新UI"""
        try:
            while True:
                data = self.data_queue.get_nowait()
                
                if data["type"] == "update":
                    # 更新分数显示
                    score = data["score"]
                    thresh = data["thresh"]
                    
                    self.var_score.set(f"匹配分: {score:.2f}")
                    self.var_thresh.set(f"阈值: {thresh:.2f}")
                    self.score_bar['value'] = score
                    
                    # 动态改变颜色：低于阈值显示红色警告（需要ttk style支持，这里简化处理）
                    
                    # 更新图片 (仅当路径变化时才重新加载，防止闪烁)
                    if not hasattr(self, 'last_img') or self.last_img != data["img"]:
                        self.update_image(data["img"])
                        self.last_img = data["img"]
                        
                elif data["type"] == "stop":
                    self.stop()
                    
        except queue.Empty:
            pass
        
        # 继续轮询
        self.root.after(100, self.update_ui_from_queue)


if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedGUI(root)
    root.mainloop()