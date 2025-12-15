#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本，验证导航器的初始化和边缘检测功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.navigator import SkyNavigator
    print("✓ 成功导入SkyNavigator类")
except ImportError as e:
    print(f"✗ 导入SkyNavigator失败: {e}")
    sys.exit(1)

try:
    import cv2
    print("✓ 成功导入cv2模块")
except ImportError as e:
    print(f"✗ 导入cv2失败: {e}")
    sys.exit(1)

try:
    import numpy as np
    print("✓ 成功导入numpy模块")
except ImportError as e:
    print(f"✗ 导入numpy失败: {e}")
    sys.exit(1)

def test_navigator_init():
    """测试导航器初始化"""
    print("\n=== 测试导航器初始化 ===")
    try:
        # 初始化导航器，启用边缘特征
        nav = SkyNavigator(
            "dataset/isle_dawn", 
            "dataset/isle_dawn/waypoints.json", 
            use_edge_feature=True
        )
        print("✓ 导航器初始化成功")
        print(f"✓ 加载了 {len(nav.waypoints)} 个路点")
        print(f"✓ 边缘特征检测: {'启用' if nav.use_edge_feature else '禁用'}")
        return nav
    except Exception as e:
        print(f"✗ 导航器初始化失败: {e}")
        return None

def test_edge_detection():
    """测试边缘检测功能"""
    print("\n=== 测试边缘检测 ===")
    try:
        # 创建一个简单的测试图像
        test_img = np.zeros((360, 640, 3), dtype=np.uint8)
        # 绘制一些简单的形状
        cv2.rectangle(test_img, (100, 100), (200, 200), (255, 255, 255), -1)
        cv2.circle(test_img, (300, 200), 50, (255, 255, 255), -1)
        cv2.line(test_img, (400, 100), (500, 300), (255, 255, 255), 5)
        
        print("✓ 创建测试图像成功")
        
        # 初始化导航器
        nav = SkyNavigator(
            "dataset/isle_dawn", 
            "dataset/isle_dawn/waypoints.json", 
            use_edge_feature=True
        )
        
        # 测试预处理函数
        processed_img = nav._preprocess(test_img)
        print(f"✓ 边缘检测成功，处理后的图像形状: {processed_img.shape}")
        
        # 检查边缘检测是否生成了非零值
        if np.sum(processed_img) > 0:
            print("✓ 边缘检测生成了有效的边缘数据")
        else:
            print("✗ 边缘检测未能生成有效边缘数据")
            
        return True
    except Exception as e:
        print(f"✗ 边缘检测测试失败: {e}")
        return False

def test_load_waypoint():
    """测试加载路点功能"""
    print("\n=== 测试加载路点 ===")
    try:
        nav = SkyNavigator(
            "dataset/isle_dawn", 
            "dataset/isle_dawn/waypoints.json", 
            use_edge_feature=True
        )
        
        # 测试加载第一个路点
        result = nav.load_waypoint(0)
        if result:
            print("✓ 加载第一个路点成功")
        else:
            print("✗ 加载第一个路点失败")
            return False
        
        # 检查是否成功提取了特征点
        if nav.target_kp and len(nav.target_kp) > 0:
            print(f"✓ 成功提取了 {len(nav.target_kp)} 个特征点")
        else:
            print("✗ 未能提取特征点")
            return False
        
        # 测试加载第二个路点
        result2 = nav.load_waypoint(1)
        if result2:
            print("✓ 加载第二个路点成功")
        else:
            print("✗ 加载第二个路点失败")
            return False
        
        return True
    except Exception as e:
        print(f"✗ 加载路点测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 光遇自动导航系统 - 核心功能测试 ===")
    
    # 运行所有测试
    results = []
    
    nav = test_navigator_init()
    results.append(nav is not None)
    
    edge_test = test_edge_detection()
    results.append(edge_test)
    
    load_test = test_load_waypoint()
    results.append(load_test)
    
    # 统计测试结果
    passed = sum(results)
    total = len(results)
    
    print(f"\n=== 测试结果汇总 ===")
    print(f"通过: {passed}/{total} 个测试")
    
    if passed == total:
        print("🎉 所有测试通过！核心功能正常！")
        return 0
    else:
        print("❌ 部分测试失败，请检查代码！")
        return 1

if __name__ == "__main__":
    sys.exit(main())