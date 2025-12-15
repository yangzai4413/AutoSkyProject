#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光遇辅助程序主入口
实现视觉导航核心的集成测试
"""

import cv2
import numpy as np
import time
from mss import mss
from core.navigator import SkyNavigator


def screen_capture():
    """
    使用mss库进行屏幕截图
    
    Returns:
        numpy.ndarray: 屏幕截图
    """
    with mss() as sct:
        # 捕获整个屏幕
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        # 转换为OpenCV格式
        img = np.array(screenshot)
        # 转换颜色空间 (BGRA to BGR)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img


def main():
    """
    主函数
    """
    print("=== 光遇辅助程序 - 视觉导航测试 ===")
    
    # 初始化导航器
    nav = SkyNavigator("dataset/isle_dawn", "dataset/isle_dawn/waypoints.json")
    
    # 创建OpenCV窗口
    cv2.namedWindow("Sky Auto Navigator", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Sky Auto Navigator", 800, 600)
    
    print("\n按 'q' 键退出测试")
    print("按 'n' 键切换到下一个目标")
    print("按 'p' 键切换到上一个目标")
    
    try:
        while True:
            # 1. 屏幕截图
            start_time = time.time()
            screen = screen_capture()
            capture_time = time.time() - start_time
            
            # 2. 计算偏移量
            offset_x, similarity = nav.calculate_offset(screen)
            process_time = time.time() - start_time - capture_time
            
            # 3. 获取当前动作
            current_action = nav.get_current_action()
            
            # 4. 创建显示图像
            display_img = screen.copy()
            
            # 5. 绘制调试信息
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            font_color = (0, 255, 0)
            thickness = 2
            line_type = cv2.LINE_AA
            
            # 导航信息
            info_text = [
                f"Target ID: {nav.current_idx} / {len(nav.waypoints) - 1}",
                f"Action: {current_action['action']} {current_action.get('description', '')}",
                f"Offset X: {offset_x:+.2f} (正数向右，负数向左)",
                f"Score: {similarity:.2f}",
                f"Capture Time: {capture_time:.3f}s",
                f"Process Time: {process_time:.3f}s",
                f"Total Time: {time.time() - start_time:.3f}s"
            ]
            
            # 显示导航信息
            y_pos = 30
            for text in info_text:
                cv2.putText(display_img, text, (10, y_pos), font, font_scale, font_color, thickness, line_type)
                y_pos += 25
            
            # 绘制中心参考线
            height, width = display_img.shape[:2]
            cv2.line(display_img, (width//2, 0), (width//2, height), (255, 0, 0), 1)
            cv2.line(display_img, (0, height//2), (width, height//2), (255, 0, 0), 1)
            
            # 绘制偏移指示线
            offset_pixel = int(offset_x)
            cv2.line(display_img, (width//2, height//2), (width//2 + offset_pixel, height//2), (0, 0, 255), 2)
            
            # 6. 显示结果
            cv2.imshow("Sky Auto Navigator", display_img)
            
            # 7. 检查按键
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                # 退出测试
                print("测试结束")
                break
            elif key == ord('n'):
                # 切换到下一个目标
                nav.next_waypoint()
            elif key == ord('p'):
                # 切换到上一个目标
                nav.load_waypoint(max(0, nav.current_idx - 1))
            
            # 8. 检查是否到达目标
            if nav.check_arrival(similarity):
                print(f"到达目标 ID: {nav.current_idx}，准备切换到下一个目标")
                nav.next_waypoint()
            
            # 限制帧率
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n测试中断")
    finally:
        # 清理资源
        cv2.destroyAllWindows()
        print("=== 测试完成 ===")


if __name__ == "__main__":
    main()