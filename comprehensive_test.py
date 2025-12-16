#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光遇辅助程序全面功能测试脚本
验证各项功能是否正常实现
"""

import os
import sys
import time
import datetime
import json

# 依赖检查
try:
    from main import is_admin
    HAS_MAIN = True
except ImportError:
    HAS_MAIN = False
    
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    
try:
    from core.vision import VisionSystem
    HAS_VISION = True
except ImportError as e:
    HAS_VISION = False
    VISION_ERROR = str(e)
    
try:
    from core.input_emul import InputManager
    HAS_INPUT = True
except ImportError as e:
    HAS_INPUT = False
    INPUT_ERROR = str(e)
    
try:
    from core.navigator import SkyNavigator
    HAS_NAVIGATOR = True
except ImportError as e:
    HAS_NAVIGATOR = False
    NAVIGATOR_ERROR = str(e)
    
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

class TestResult:
    """测试结果类，用于记录测试情况"""
    def __init__(self, test_name):
        self.test_name = test_name
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.status = "pending"
        self.message = ""
        self.details = []
        
    def passed(self, message=""):
        """标记测试通过"""
        self.status = "passed"
        self.message = message
        self.end_time = datetime.datetime.now()
        
    def failed(self, message=""):
        """标记测试失败"""
        self.status = "failed"
        self.message = message
        self.end_time = datetime.datetime.now()
        
    def add_detail(self, detail):
        """添加测试细节"""
        self.details.append(detail)
        
    def get_duration(self):
        """获取测试持续时间"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

class ComprehensiveTest:
    """全面测试类"""
    def __init__(self):
        self.test_results = []
        
        # 安全获取管理员权限状态
        admin_status = False
        if HAS_MAIN:
            admin_status = is_admin()
        
        self.test_data = {
            "app_version": "1.0.0",
            "test_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_environment": {
                "is_admin": admin_status,
                "python_version": sys.version,
                "os_name": sys.platform,
                "cwd": os.getcwd()
            }
        }
        
    def add_test_result(self, result):
        """添加测试结果"""
        self.test_results.append(result)
        
    def run_test(self, test_func, test_name):
        """运行单个测试"""
        result = TestResult(test_name)
        self.add_test_result(result)
        
        print(f"\n=== 测试：{test_name} ===")
        
        try:
            # 运行测试函数
            success, message = test_func(result)
            if success:
                result.passed(message)
                print(f"✅ 测试通过: {message}")
            else:
                result.failed(message)
                print(f"❌ 测试失败: {message}")
        except Exception as e:
            result.failed(f"测试异常: {str(e)}")
            print(f"❌ 测试异常: {str(e)}")
        
        duration = result.get_duration()
        print(f"测试耗时: {duration:.2f}秒")
        
    def generate_report(self):
        """生成测试报告"""
        # 汇总统计
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.status == "passed")
        failed = sum(1 for r in self.test_results if r.status == "failed")
        
        # 生成Markdown报告
        report = "# 光遇辅助程序功能测试报告\n\n"
        report += f"## 测试基本信息\n"
        report += f"- 测试日期: {self.test_data['test_date']}\n"
        report += f"- 应用版本: {self.test_data['app_version']}\n"
        report += f"- 测试环境: {self.test_data['test_environment']['os_name']}\n"
        report += f"- Python版本: {self.test_data['test_environment']['python_version']}\n"
        report += f"- 管理员权限: {'是' if self.test_data['test_environment']['is_admin'] else '否'}\n\n"
        
        report += "## 测试结果汇总\n"
        report += f"| 总测试数 | 通过 | 失败 | 通过率 |\n"
        report += f"|---------|------|------|--------|\n"
        report += f"| {total} | {passed} | {failed} | {passed/total*100:.1f}% |\n\n"
        
        report += "## 详细测试结果\n\n"
        
        for result in self.test_results:
            status_emoji = "✅" if result.status == "passed" else "❌"
            report += f"### {status_emoji} {result.test_name}\n"
            report += f"- **状态**: {result.status}\n"
            report += f"- **耗时**: {result.get_duration():.2f}秒\n"
            report += f"- **结果**: {result.message}\n"
            
            if result.details:
                report += "- **详细信息**:\n"
                for detail in result.details:
                    report += f"  - {detail}\n"
            report += "\n"
        
        # 写入报告文件
        report_filename = f"test_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n=== 测试报告生成完成 ===")
        print(f"报告文件: {report_filename}")
        
        return report_filename

    # 测试函数
    def test_admin_permission(self, result):
        """测试管理员权限"""
        if not HAS_MAIN:
            return False, "无法导入main模块，管理员权限检查无法进行"
            
        has_admin = is_admin()
        result.add_detail(f"当前管理员权限: {has_admin}")
        
        if has_admin:
            return True, "管理员权限检查通过"
        else:
            return False, "缺少管理员权限，可能影响部分功能"
    
    def test_window_detection(self, result):
        """测试窗口检测功能"""
        if not HAS_VISION:
            return False, f"无法导入VisionSystem: {VISION_ERROR}"
            
        try:
            vision = VisionSystem(window_title="Sky")
            result.add_detail("VisionSystem实例化成功")
            
            # 测试窗口位置更新
            window_found = vision.update_window_region()
            result.add_detail(f"游戏窗口检测: {'成功' if window_found else '失败'}")
            
            if window_found:
                result.add_detail(f"窗口区域: {vision.game_region}")
                return True, "游戏窗口检测功能正常"
            else:
                return False, "未检测到游戏窗口，可能需要手动调整窗口标题"
        except Exception as e:
            return False, f"窗口检测失败: {str(e)}"
    
    def test_screenshot_function(self, result):
        """测试截屏功能"""
        if not HAS_VISION:
            return False, f"无法导入VisionSystem: {VISION_ERROR}"
            
        try:
            vision = VisionSystem(window_title="Sky")
            result.add_detail("VisionSystem实例化成功")
            
            # 测试区域截屏
            frame = vision.capture_screen()
            result.add_detail(f"截屏成功，尺寸: {frame.shape[:2]}")
            
            # 检查截屏是否有效
            if frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
                return True, "区域截屏功能正常"
            else:
                return False, "截屏结果无效，可能是窗口检测问题"
        except Exception as e:
            return False, f"截屏功能失败: {str(e)}"
    
    def test_edge_detection(self, result):
        """测试边缘检测功能"""
        if not HAS_VISION:
            return False, f"无法导入VisionSystem: {VISION_ERROR}"
        if not HAS_NUMPY:
            return False, "无法导入numpy，边缘检测结果分析无法进行"
            
        try:
            vision = VisionSystem(window_title="Sky")
            result.add_detail("VisionSystem实例化成功")
            
            # 截取一帧画面
            frame = vision.capture_screen()
            result.add_detail(f"获取测试帧，尺寸: {frame.shape[:2]}")
            
            # 测试边缘检测
            edges = vision._preprocess(frame)
            result.add_detail(f"边缘检测完成，尺寸: {edges.shape[:2]}")
            
            # 检查边缘检测结果
            edge_pixels = np.sum(edges > 0)
            result.add_detail(f"边缘像素数量: {edge_pixels}")
            
            if edge_pixels > 0:
                return True, "边缘检测功能正常，成功提取边缘特征"
            else:
                return False, "边缘检测结果为空，可能是阈值设置问题"
        except Exception as e:
            return False, f"边缘检测功能失败: {str(e)}"
    
    def test_navigator_init(self, result):
        """测试导航器初始化"""
        if not HAS_NAVIGATOR:
            return False, f"无法导入SkyNavigator: {NAVIGATOR_ERROR}"
            
        try:
            # 测试导航器初始化
            nav = SkyNavigator(
                "dataset/isle_dawn", 
                "dataset/isle_dawn/waypoints.json", 
                use_edge_feature=True
            )
            result.add_detail("SkyNavigator实例化成功")
            
            # 检查路点加载
            waypoint_count = len(nav.waypoints)
            result.add_detail(f"路点加载数量: {waypoint_count}")
            
            # 检查边缘特征设置
            result.add_detail(f"边缘特征启用: {nav.use_edge_feature}")
            
            if waypoint_count > 0:
                return True, "导航器初始化成功，路点加载正常"
            else:
                return False, "导航器初始化成功，但未加载到路点"
        except Exception as e:
            return False, f"导航器初始化失败: {str(e)}"
    
    def test_input_manager(self, result):
        """测试输入管理器"""
        if not HAS_INPUT:
            return False, f"无法导入InputManager: {INPUT_ERROR}"
            
        try:
            input_mgr = InputManager(window_title="Sky")
            result.add_detail("InputManager实例化成功")
            
            # 测试窗口焦点功能
            focus_result = input_mgr.focus_game_window()
            result.add_detail(f"窗口焦点设置: {'成功' if focus_result else '失败'}")
            
            return True, "输入管理器功能正常"
        except Exception as e:
            return False, f"输入管理器测试失败: {str(e)}"
    
    def test_file_structure(self, result):
        """测试文件结构完整性"""
        required_files = [
            "core/navigator.py",
            "core/vision.py", 
            "core/input_emul.py",
            "main.py",
            "dataset/isle_dawn/waypoints.json"
        ]
        
        missing_files = []
        for file_path in required_files:
            if os.path.exists(file_path):
                result.add_detail(f"✓ {file_path} 存在")
            else:
                missing_files.append(file_path)
                result.add_detail(f"✗ {file_path} 缺失")
        
        if not missing_files:
            return True, "所有必要文件存在"
        else:
            return False, f"缺少必要文件: {', '.join(missing_files)}"
    
    def test_dependency_check(self, result):
        """测试依赖项检查"""
        dependencies = [
            ("cv2", HAS_CV2, "OpenCV，用于图像处理"),
            ("numpy", HAS_NUMPY, "数值计算库"),
            ("VisionSystem", HAS_VISION, "视觉系统，用于截屏和边缘检测"),
            ("InputManager", HAS_INPUT, "输入管理器，用于控制游戏"),
            ("SkyNavigator", HAS_NAVIGATOR, "导航器，用于路径规划"),
        ]
        
        result.add_detail("依赖项检查结果:")
        missing_deps = []
        
        for dep_name, has_dep, description in dependencies:
            status = "✓ 已安装" if has_dep else "✗ 缺失"
            result.add_detail(f"  - {dep_name}: {status} ({description})")
            if not has_dep:
                missing_deps.append(dep_name)
        
        if not missing_deps:
            return True, "所有依赖项已安装"
        else:
            return False, f"缺少依赖项: {', '.join(missing_deps)}"

# 主测试执行
if __name__ == "__main__":
    print("=== 光遇辅助程序全面功能测试 ===")
    print(f"测试开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test = ComprehensiveTest()
    
    # 运行各项测试
    test.run_test(test.test_dependency_check, "依赖项检查")
    test.run_test(test.test_admin_permission, "管理员权限检查")
    test.run_test(test.test_file_structure, "文件结构完整性")
    
    # 只有在依赖存在时才运行对应的测试
    if HAS_NAVIGATOR:
        test.run_test(test.test_navigator_init, "导航器初始化")
    
    if HAS_VISION:
        test.run_test(test.test_window_detection, "游戏窗口检测")
        test.run_test(test.test_screenshot_function, "区域截屏功能")
        if HAS_NUMPY:
            test.run_test(test.test_edge_detection, "边缘检测功能")
    
    if HAS_INPUT:
        test.run_test(test.test_input_manager, "输入管理器功能")
    
    # 生成测试报告
    report_file = test.generate_report()
    
    print(f"\n=== 测试完成 ===")
    print(f"报告已保存到: {report_file}")
    print(f"请使用Markdown阅读器打开查看详细报告")
