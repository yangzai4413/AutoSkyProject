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
from core.input_controller import InputController


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


# 假设你的数据集图片是 640x360
DATASET_WIDTH = 640
DATASET_HEIGHT = 360


def capture_and_resize():
    """
    截取全屏并缩放到标准处理分辨率
    """
    # 1. 获取全屏截图
    screenshot = screen_capture()
    
    # 2. 强制缩放 (解决分辨率适配问题)
    # 无论屏幕是 1920x1080 还是 2560x1440，都压扁到 640x360 进行处理
    # 这样 offset 的单位永远是基于 640 宽度的，不需要动态调整 PID 参数
    resized_frame = cv2.resize(screenshot, (DATASET_WIDTH, DATASET_HEIGHT))
    
    return resized_frame


def main_loop(stop_event, status_callback=None):
    """
    主循环函数，接受停止事件和状态回调
    
    Args:
        stop_event: 用于停止循环的事件对象
        status_callback: 状态回调函数，用于实时汇报状态
    """
    print("导航线程启动")
    
    try:
        # 初始化导航器和输入控制器
        nav = SkyNavigator("dataset/isle_dawn", "dataset/isle_dawn/waypoints.json")
        ctrl = InputController()
        
        # 初始状态
        is_moving = False
        
        # 初始校准：发送第一张路点图给 UI
        if status_callback:
            first_wp = nav.waypoints[0]
            first_img_path = os.path.join(nav.dataset_path, first_wp['img_name'])
            status_callback(first_img_path, 0.0, 0.0)
        
        print("开始初始校准...")
        # 运行初始校准
        calibrated = _initial_calibration(nav, ctrl, stop_event, status_callback)
        
        if not calibrated:
            print("校准失败，停止运行")
            return
        
        print("校准成功，开始导航")
        
        while not stop_event.is_set():
            # 1. 屏幕截图 & 缩放
            frame = capture_and_resize() # 确保返回的是 (640, 360) 的图
            
            # 2. 计算偏移量
            offset_x, similarity = nav.calculate_offset(frame)
            current_thresh = nav.waypoints[nav.current_idx].get('match_threshold', 0.6)
            
            # 3. 汇报状态给 UI
            if status_callback:
                # 获取当前目标图片的绝对路径
                wp = nav.waypoints[nav.current_idx]
                img_path = os.path.join(nav.dataset_path, wp['img_name'])
                
                status_callback(img_path, similarity, current_thresh)
            
            # 4. 检查是否到达目标
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
            
            # 5. 自动视角调整
            # 只有在非盲飞模式下才调整视角
            if not nav.is_blind():
                ctrl.align_camera(offset_x)
            
            # 6. 保持前进
            if not is_moving:
                is_moving = True
                ctrl.move_forward()
            
            # 7. 限制帧率
            time.sleep(0.1)
            
    except Exception as e:
        print(f"运行出错: {e}")
    finally:
        # 确保异常退出时UI状态重置
        print("清理资源...")
        ctrl.stop_all_movement()


def _initial_calibration(nav, ctrl, stop_event, status_callback=None):
    """
    初始校准：寻找匹配的环境
    
    Args:
        nav: SkyNavigator 实例
        ctrl: InputController 实例
        stop_event: 停止事件
        status_callback: 状态回调
        
    Returns:
        bool: 校准成功返回 True，否则返回 False
    """
    search_attempts = 0
    
    while not stop_event.is_set():
        # 1. 看一眼
        frame = capture_and_resize()
        offset, score = nav.calculate_offset(frame)
        
        # 2. 汇报状态
        if status_callback:
            wp = nav.waypoints[nav.current_idx]
            img_path = os.path.join(nav.dataset_path, wp['img_name'])
            status_callback(img_path, score, 0.6)  # 校准阈值固定为0.6
        
        # 3. 判断
        if score > 0.6: # 找到了高置信度的匹配
            print(f"校准成功！当前匹配分: {score:.2f}")
            # 进行微调，把视角对正
            if abs(offset) > 10:
                ctrl.align_camera(offset)
                time.sleep(0.5)
                continue
            return True # 进入正式导航
            
        # 4. 没找到，尝试原地旋转寻找
        print(f"未找到目标 (Score: {score:.2f})，正在搜索环境...")
        # 向右转一点
        ctrl.align_camera(30)
        time.sleep(0.5) # 等画面稳定
        
        search_attempts += 1
        if search_attempts > 12: # 转了一圈也没找到
            print("校准失败：请手动移动角色到近似起始位置")
            return False


def main():
    """
    主函数 - 用于测试和调试
    """
    print("=== 光遇辅助程序 - 视觉导航测试 ===")
    
    # 初始化导航器 - 启用边缘特征
    nav = SkyNavigator("dataset/isle_dawn", "dataset/isle_dawn/waypoints.json", use_edge_feature=True)
    
    # 初始化输入控制器
    ctrl = InputController()
    
    # 创建OpenCV窗口
    cv2.namedWindow("Sky Auto Navigator", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Sky Auto Navigator", 800, 600)
    
    print("\n按 'q' 键退出测试")
    print("按 'n' 键切换到下一个目标")
    print("按 'p' 键切换到上一个目标")
    print("按 'w' 键开始移动")
    print("按 's' 键停止移动")
    print("按 'a' 键左移")
    print("按 'd' 键右移")
    print("按 'space' 键跳跃/飞行")
    
    try:
        # 初始状态
        is_moving = False
        is_moving_left = False
        is_moving_right = False
        blind_mode = False
        
        while True:
            # 1. 屏幕截图 & 缩放
            start_time = time.time()
            screen = capture_and_resize()  # 使用新的归一化截图函数
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
                f"Consecutive Misses: {nav.consecutive_misses}",
                f"Blind Mode: {'On' if nav.is_blind() else 'Off'}",
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
                ctrl.stop_all_movement()
                break
            elif key == ord('n'):
                # 切换到下一个目标
                nav.next_waypoint()
            elif key == ord('p'):
                # 切换到上一个目标
                nav.load_waypoint(max(0, nav.current_idx - 1))
            elif key == ord('w'):
                # 开始/停止前进
                is_moving = not is_moving
                if is_moving:
                    print("开始移动")
                    ctrl.move_forward()
                else:
                    print("停止移动")
                    ctrl.stop_moving()
            elif key == ord('a'):
                # 开始/停止左移
                is_moving_left = not is_moving_left
                if is_moving_left:
                    print("开始左移")
                    ctrl.move_left()
                else:
                    print("停止左移")
                    ctrl.stop_moving()
            elif key == ord('d'):
                # 开始/停止右移
                is_moving_right = not is_moving_right
                if is_moving_right:
                    print("开始右移")
                    ctrl.move_right()
                else:
                    print("停止右移")
                    ctrl.stop_moving()
            elif key == ord('s'):
                # 停止所有移动
                is_moving = False
                is_moving_left = False
                is_moving_right = False
                print("停止所有移动")
                ctrl.stop_all_movement()
            elif key == ord(' '):
                # 跳跃/飞行
                print("跳跃/飞行")
                ctrl.jump()
                time.sleep(0.1)
            
            # 8. 自动视角调整
            # 只有在非盲飞模式下才调整视角
            if not nav.is_blind():
                ctrl.align_camera(offset_x)
            
            # 9. 检查是否到达目标
            if nav.check_arrival(similarity):
                print(f"到达目标 ID: {nav.current_idx}")
                # 执行路点定义的特殊动作
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
            
            # 10. 限制帧率
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n测试中断")
    finally:
        # 清理资源
        cv2.destroyAllWindows()
        ctrl.stop_all_movement()
        print("=== 测试完成 ===")


if __name__ == "__main__":
    main()