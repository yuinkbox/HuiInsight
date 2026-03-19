"""
主管大屏 - 实时监控仪表盘
基于 PyQt6 的高管监控界面，仅限 SUPERVISOR 权限访问

设计原则：
1. 冷峻专业风格，暗黑科技主题
2. 数据驱动，增量刷新
3. 颜色编码，智能排序
4. 权限隔离，安全访问
"""

import sys
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# PyQt6 导入
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
        QLabel, QMessageBox, QProgressBar
    )
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
    from PyQt6.QtGui import QFont, QColor, QBrush, QPalette
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    # 降级处理：如果无PyQt环境，提供模拟接口
    class QMainWindow: pass
    class QWidget: pass
    class QTableWidget: pass
    class QTimer: pass
    class pyqtSignal: pass

logger = logging.getLogger(__name__)

# PyQt6 不可用时提供空壳 QColor，避免 ColorScheme 类定义崩溃
if not PYQT_AVAILABLE:
    class QColor:
        def __init__(self, *args): pass
    class QBrush:
        def __init__(self, *args): pass
    class Qt:
        class AlignmentFlag: pass
        class ItemFlag:
            ItemIsEditable = 0
        class GlobalColor:
            red = None
            black = None
    class QPalette:
        class ColorRole: pass
    class QFont:
        def __init__(self, *args): pass
        def setPointSize(self, *args): pass


# ==================== 颜色方案配置 ====================
class ColorScheme:
    """冷峻科技感配色方案"""
    
    # 暗黑主题基础色
    BACKGROUND_DARK = QColor(30, 30, 40)      # 深灰蓝背景
    BACKGROUND_TABLE = QColor(40, 40, 50)     # 表格背景
    FOREGROUND_LIGHT = QColor(220, 220, 230)  # 浅灰文字
    
    # 状态颜色编码
    COLOR_NORMAL = QColor(100, 150, 200)      # 正常 - 科技蓝
    COLOR_SUSPICIOUS = QColor(220, 80, 80)    # 可疑 - 警示红
    COLOR_SUDDEN_ISSUE = QColor(255, 140, 0)  # 突发问题 - 橙色
    COLOR_RISK_TRACKING = QColor(80, 200, 120)# 风险追踪 - 安全绿
    COLOR_EXEMPTED = QColor(120, 160, 220)    # 豁免 - 浅蓝
    
    # 表格行颜色
    ROW_SUSPICIOUS = QColor(40, 20, 20)       # 可疑行背景（深红）
    ROW_EXEMPTED = QColor(20, 30, 40)         # 豁免行背景（深蓝）
    ROW_NORMAL = QColor(40, 40, 50)           # 正常行背景
    
    @staticmethod
    def get_status_color(status: str) -> QColor:
        """根据审计状态获取对应颜色"""
        color_map = {
            "normal": ColorScheme.COLOR_NORMAL,
            "suspicious": ColorScheme.COLOR_SUSPICIOUS,
            "sudden_issue": ColorScheme.COLOR_SUDDEN_ISSUE,
            "risk_tracking": ColorScheme.COLOR_RISK_TRACKING,
            "exempted": ColorScheme.COLOR_EXEMPTED,
        }
        return color_map.get(status, ColorScheme.COLOR_NORMAL)
    
    @staticmethod
    def get_row_color(status: str) -> QColor:
        """根据审计状态获取行背景色"""
        if status == "suspicious":
            return ColorScheme.ROW_SUSPICIOUS
        elif status in ["exempted", "risk_tracking"]:
            return ColorScheme.ROW_EXEMPTED
        else:
            return ColorScheme.ROW_NORMAL


# ==================== API 客户端线程 ====================
class APIClientThread(QThread):
    """
    API 数据获取线程
    
    设计原则：
    1. 后台线程获取数据，避免UI卡顿
    2. 错误处理与重试机制
    3. 信号驱动UI更新
    """
    
    # 定义信号
    data_received = pyqtSignal(dict)      # 数据接收成功
    data_error = pyqtSignal(str)          # 数据获取失败
    progress_update = pyqtSignal(int)     # 进度更新
    
    def __init__(self, api_url: str, access_token: str):
        """
        初始化API客户端线程
        
        Args:
            api_url: 后端API地址
            access_token: 访问令牌
        """
        super().__init__()
        self.api_url = api_url.rstrip('/')
        self.access_token = access_token
        self._running = False
        
        # 请求头
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def run(self):
        """主线程循环"""
        self._running = True
        
        while self._running:
            try:
                self._fetch_data()
                # 线程由外部定时器控制，不在此处sleep
                break  # 单次执行
                
            except Exception as e:
                logger.error(f"API线程异常: {e}")
                self.data_error.emit(str(e))
                break
    
    def stop(self):
        """停止线程"""
        self._running = False
    
    def _fetch_data(self):
        """获取实时状态数据"""
        import requests
        
        try:
            self.progress_update.emit(30)  # 开始获取
            
            # 调用后端API
            response = requests.get(
                f"{self.api_url}/api/supervisor/realtime-status",
                headers=self.headers,
                timeout=10  # 10秒超时
            )
            
            self.progress_update.emit(70)  # 数据接收
            
            if response.status_code == 200:
                data = response.json()
                self.data_received.emit(data)
                self.progress_update.emit(100)  # 完成
            elif response.status_code == 403:
                self.data_error.emit("权限不足：只有主管可以访问此功能")
            else:
                self.data_error.emit(f"API请求失败: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.data_error.emit("请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            self.data_error.emit("连接失败，请检查后端服务状态")
        except Exception as e:
            self.data_error.emit(f"数据获取异常: {str(e)}")


# ==================== 状态栏组件 ====================
class StatusHeader(QWidget):
    """
    状态栏组件 - 顶部信息展示
    
    功能：
    1. 系统状态显示
    2. 强制刷新按钮
    3. 进度指示
    """
    
    def __init__(self, parent=None):
        """初始化状态栏"""
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI布局"""
        layout = QHBoxLayout(self)
        
        # 左侧：状态信息
        self.status_label = QLabel("系统状态: 正在初始化...")
        self.status_label.setStyleSheet("color: #A0A0B0; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()  # 弹性空间
        
        # 中间：进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #505060;
                border-radius: 3px;
                background-color: #303040;
            }
            QProgressBar::chunk {
                background-color: #4A90E2;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 右侧：刷新按钮
        self.refresh_button = QPushButton("⟳ 强制刷新")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3A506B;
                color: #FFFFFF;
                border: 1px solid #505060;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4A6090;
            }
            QPushButton:pressed {
                background-color: #2A4060;
            }
        """)
        layout.addWidget(self.refresh_button)
        
        self.setLayout(layout)
    
    def update_status(self, text: str, is_error: bool = False):
        """更新状态文本"""
        color = "#FF6B6B" if is_error else "#A0A0B0"
        self.status_label.setText(f"系统状态: {text}")
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px;")
    
    def update_progress(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)


# ==================== 实时雷达表格组件 ====================
class RadarTable(QTableWidget):
    """
    实时雷达表格 - 核心监控组件
    
    特性：
    1. 颜色编码渲染
    2. 智能排序（可疑行置顶）
    3. 增量刷新
    4. 性能优化
    """
    
    # 列定义
    COLUMNS = [
        ("员工姓名", 120),
        ("申报状态", 100),
        ("真实房间", 100),
        ("停留时长", 90),
        ("智能判定", 100),
        ("异常原因", 300)
    ]
    
    def __init__(self, parent=None):
        """初始化雷达表格"""
        super().__init__(parent)
        self._setup_table()
        
        # 数据缓存（用于增量更新）
        self._user_data_cache = {}  # {user_id: row_data}
        self._suspicious_rows = []  # 可疑行索引列表
    
    def _setup_table(self):
        """设置表格属性"""
        # 设置列
        self.setColumnCount(len(self.COLUMNS))
        for col, (name, width) in enumerate(self.COLUMNS):
            self.setHorizontalHeaderItem(col, QTableWidgetItem(name))
            self.setColumnWidth(col, width)
        
        # 表格样式
        self.setStyleSheet("""
            QTableWidget {
                background-color: #282838;
                color: #D0D0E0;
                gridline-color: #404050;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #2A2A3A;
                color: #B0B0C0;
                padding: 6px;
                border: 1px solid #404050;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)
        
        # 性能优化
        self.setAlternatingRowColors(False)
        self.setSortingEnabled(False)  # 自定义排序逻辑
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        
        # 设置行高
        self.verticalHeader().setDefaultSectionSize(32)
    
    def update_data(self, active_users: List[Dict[str, Any]]):
        """
        更新表格数据（增量刷新）
        
        Args:
            active_users: 活跃用户数据列表
        """
        # 保存当前滚动位置
        scroll_value = self.verticalScrollBar().value()
        
        try:
            # 开始批量更新（避免闪烁）
            self.setUpdatesEnabled(False)
            
            # 清空可疑行记录
            self._suspicious_rows.clear()
            
            # 设置行数
            row_count = len(active_users)
            self.setRowCount(row_count)
            
            # 填充数据
            for row, user_data in enumerate(active_users):
                self._update_row(row, user_data)
                
                # 记录可疑行
                if user_data.get("status") == "suspicious":
                    self._suspicious_rows.append(row)
            
            # 可疑行置顶排序
            self._sort_suspicious_to_top()
            
            # 恢复滚动位置
            self.verticalScrollBar().setValue(scroll_value)
            
        finally:
            self.setUpdatesEnabled(True)
            self.viewport().update()
    
    def _update_row(self, row: int, user_data: Dict[str, Any]):
        """
        更新单行数据
        
        Args:
            row: 行索引
            user_data: 用户数据
        """
        user_id = user_data.get("user_id", 0)
        
        # 缓存数据（用于增量更新判断）
        self._user_data_cache[user_id] = user_data
        
        # 填充各列数据
        items = [
            user_data.get("full_name", "未知"),
            user_data.get("status", "unknown"),
            user_data.get("room_id", "N/A"),
            self._format_duration(user_data.get("stay_duration", 0)),
            self._get_status_display(user_data.get("status", "normal")),
            user_data.get("context_reason", "")
        ]
        
        for col, text in enumerate(items):
            item = QTableWidgetItem(str(text))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 设置颜色
            self._apply_cell_style(item, col, user_data)
            
            self.setItem(row, col, item)
        
        # 设置行背景色
        self._apply_row_style(row, user_data)
    
    def _apply_cell_style(self, item: QTableWidgetItem, col: int, user_data: Dict[str, Any]):
        """应用单元格样式"""
        status = user_data.get("status", "normal")
        
        # 状态列特殊着色
        if col == 4:  # 智能判定列
            color = ColorScheme.get_status_color(status)
            item.setForeground(QBrush(color))
        
        # 可疑状态特殊标记
        if status == "suspicious" and col == 0:  # 姓名列
            font = item.font()
            font.setBold(True)
            item.setFont(font)
    
    def _apply_row_style(self, row: int, user_data: Dict[str, Any]):
        """应用行样式"""
        status = user_data.get("status", "normal")
        color = ColorScheme.get_row_color(status)
        
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(QBrush(color))
    
    def _sort_suspicious_to_top(self):
        """将可疑行排序到顶部"""
        if not self._suspicious_rows:
            return
        
        # 获取所有行数据
        all_rows = []
        for row in range(self.rowCount()):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            all_rows.append((row, row_data))
        
        # 分离可疑行和正常行
        suspicious_rows = []
        normal_rows = []
        
        for row_idx, row_data in all_rows:
            if row_idx in self._suspicious_rows:
                suspicious_rows.append((row_idx, row_data))
            else:
                normal_rows.append((row_idx, row_data))
        
        # 重新排序：可疑行在前
        sorted_rows = suspicious_rows + normal_rows
        
        # 更新表格数据
        for new_row, (old_row, row_data) in enumerate(sorted_rows):
            for col, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.setItem(new_row, col, item)
            
            # 重新应用样式
            user_id = self._extract_user_id(row_data)
            if user_id in self._user_data_cache:
                self._apply_row_style(new_row, self._user_data_cache[user_id])
    
    def _extract_user_id(self, row_data: List[str]) -> int:
        """从行数据中提取用户ID（简化实现）"""
        # 实际应根据数据结构调整
        try:
            # 假设第一列包含用户ID信息
            name_text = row_data[0]
            if "(" in name_text and ")" in name_text:
                user_id_str = name_text.split("(")[1].split(")")[0]
                return int(user_id_str)
        except:
            pass
        return 0
    
    @staticmethod
    def _format_duration(seconds: int) -> str:
        """格式化停留时长"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}分"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}时{minutes}分"
    
    @staticmethod
    def _get_status_display(status: str) -> str:
        """获取状态显示文本"""
        status_map = {
            "normal": "正常",
            "suspicious": "可疑",
            "sudden_issue": "突发问题",
            "risk_tracking": "风险追踪",
            "exempted": "业务豁免"
        }
        return status_map.get(status, status)


# ==================== 主管大屏主窗口 ====================
class SupervisorDashboard(QMainWindow):
    """
    主管大屏主窗口
    
    权限要求：仅限 SUPERVISOR 角色访问
    刷新间隔：5000ms (5秒)
    """
    
    def __init__(self, api_url: str, access_token: str, parent=None):
        """
        初始化主管大屏
        
        Args:
            api_url: 后端API地址
            access_token: 访问令牌
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 参数验证
        if not api_url or not access_token:
            raise ValueError("API地址和访问令牌不能为空")
        
        self.api_url = api_url
        self.access_token = access_token
        
        # 初始化UI
        self._setup_ui()
        
        # 初始化定时器
        self._setup_timer()
        
        # 初始化API线程
        self.api_thread = None
        
        # 设置窗口属性
        self.setWindowTitle("AHDUNYI - 主管监控大屏")
        self.setGeometry(100, 100, 1200, 800)  # 初始大小
        
        # 应用暗黑主题
        self._apply_dark_theme()
        
        logger.info("主管大屏初始化完成")
    
    def _setup_ui(self):
        """设置主界面布局"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        
        # 1. 状态栏
        self.status_header = StatusHeader()
        main_layout.addWidget(self.status_header)
        
        # 2. 实时雷达表格
        self.radar_table = RadarTable()
        main_layout.addWidget(self.radar_table)
        
        # 3. 底部状态栏
        self.bottom_status = QLabel("最后更新: --:--:-- | 活跃用户: 0")
        self.bottom_status.setStyleSheet("color: #808090; font-size: 11px; padding: 4px;")
        main_layout.addWidget(self.bottom_status)
        
        # 连接信号
        self.status_header.refresh_button.clicked.connect(self.force_refresh)
    
    def _setup_timer(self):
        """设置定时刷新器"""
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(5000)  # 5秒间隔
        self.refresh_timer.timeout.connect(self.refresh_data)
        
        # 启动定时器
        self.refresh_timer.start()
        logger.info("定时刷新器启动，间隔5000ms")
    
    def _apply_dark_theme(self):
        """应用暗黑主题"""
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, ColorScheme.BACKGROUND_DARK)
        palette.setColor(QPalette.ColorRole.WindowText, ColorScheme.FOREGROUND_LIGHT)
        palette.setColor(QPalette.ColorRole.Base, ColorScheme.BACKGROUND_TABLE)
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(50, 50, 60))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(40, 40, 50))
        palette.setColor(QPalette.ColorRole.ToolTipText, ColorScheme.FOREGROUND_LIGHT)
        palette.setColor(QPalette.ColorRole.Text, ColorScheme.FOREGROUND_LIGHT)
        palette.setColor(QPalette.ColorRole.Button, QColor(60, 60, 70))
        palette.setColor(QPalette.ColorRole.ButtonText, ColorScheme.FOREGROUND_LIGHT)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(100, 150, 200))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(100, 150, 200))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        self.setPalette(palette)
        
        # 设置字体
        font = QFont("Microsoft YaHei UI" if sys.platform == "win32" else "Noto Sans")
        font.setPointSize(10)
        self.setFont(font)
    
    def refresh_data(self):
        """定时刷新数据"""
        if self.api_thread and self.api_thread.isRunning():
            logger.debug("API线程仍在运行，跳过本次刷新")
            return
        
        self.status_header.update_status("正在获取数据...")
        self.status_header.update_progress(0)
        
        # 创建并启动API线程
        self.api_thread = APIClientThread(self.api_url, self.access_token)
        self.api_thread.data_received.connect(self._on_data_received)
        self.api_thread.data_error.connect(self._on_data_error)
        self.api_thread.progress_update.connect(self.status_header.update_progress)
        self.api_thread.finished.connect(self._on_api_thread_finished)
        
        self.api_thread.start()
    
    def force_refresh(self):
        """强制刷新数据"""
        logger.info("强制刷新触发")
        self.refresh_data()
    
    def _on_data_received(self, data: Dict[str, Any]):
        """数据接收成功处理"""
        try:
            if not data.get("success", False):
                self._on_data_error("API返回失败状态")
                return
            
            # 更新表格数据
            active_users = data.get("active_users", [])
            self.radar_table.update_data(active_users)
            
            # 更新状态信息
            system_stats = data.get("system", {})
            total_users = system_stats.get("total_active_users", 0)
            timestamp = system_stats.get("timestamp", "")
            
            # 格式化时间
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = "--:--:--"
            else:
                time_str = "--:--:--"
            
            # 更新底部状态
            self.bottom_status.setText(
                f"最后更新: {time_str} | 活跃用户: {total_users} | "
                f"RoomMonitor: {'可用' if system_stats.get('room_monitor_available') else '不可用'} | "
                f"审计引擎: {'可用' if system_stats.get('audit_engine_available') else '不可用'}"
            )
            
            # 更新顶部状态
            self.status_header.update_status("数据更新成功")
            self.status_header.update_progress(100)
            
            logger.debug(f"数据更新成功，活跃用户: {total_users}")
            
        except Exception as e:
            logger.error(f"数据处理异常: {e}")
            self._on_data_error(f"数据处理失败: {str(e)}")
    
    def _on_data_error(self, error_msg: str):
        """数据获取失败处理"""
        logger.error(f"数据获取失败: {error_msg}")
        self.status_header.update_status(error_msg, is_error=True)
        self.status_header.update_progress(0)
        
        # 显示错误提示（非阻塞）
        QMessageBox.warning(
            self,
            "数据获取失败",
            f"无法获取实时监控数据:\n{error_msg}\n\n请检查网络连接和后端服务状态。",
            QMessageBox.StandardButton.Ok
        )
    
    def _on_api_thread_finished(self):
        """API线程完成处理"""
        self.api_thread = None
        logger.debug("API线程执行完成")
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        logger.info("主管大屏正在关闭...")
        
        # 停止定时器
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        
        # 停止API线程
        if self.api_thread and self.api_thread.isRunning():
            self.api_thread.stop()
            self.api_thread.wait(2000)  # 等待2秒
        
        event.accept()
        logger.info("主管大屏已关闭")


# ==================== 工厂函数与权限验证 ====================
def create_supervisor_dashboard(api_url: str, access_token: str, user_role: str) -> Optional[SupervisorDashboard]:
    """
    创建主管大屏实例（带权限验证）
    
    Args:
        api_url: 后端API地址
        access_token: 访问令牌
        user_role: 用户角色
        
    Returns:
        SupervisorDashboard实例（如果权限验证通过）
        None（如果权限不足或环境不支持）
    """
    # 权限验证
    if user_role != "SUPERVISOR":
        logger.warning(f"权限不足：用户角色 {user_role} 无法访问主管大屏")
        return None
    
    # 环境检查
    if not PYQT_AVAILABLE:
        logger.warning("PyQt6不可用，无法创建GUI界面")
        return None
    
    try:
        dashboard = SupervisorDashboard(api_url, access_token)
        return dashboard
    except Exception as e:
        logger.error(f"创建主管大屏失败: {e}")
        return None


def launch_supervisor_dashboard(api_url: str, access_token: str, user_role: str):
    """
    启动主管大屏应用
    
    Args:
        api_url: 后端API地址
        access_token: 访问令牌
        user_role: 用户角色
    """
    # 权限验证
    if user_role != "SUPERVISOR":
        print("错误：只有主管(SUPERVISOR)可以访问此功能")
        return
    
    # 环境检查
    if not PYQT_AVAILABLE:
        print("错误：PyQt6不可用，请安装: pip install PyQt6")
        return
    
    try:
        # 创建应用实例
        app = QApplication(sys.argv)
        
        # 创建主管大屏
        dashboard = SupervisorDashboard(api_url, access_token)
        dashboard.show()
        
        # 执行应用
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"启动主管大屏失败: {e}")


# ==================== 命令行测试 ====================
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试参数
    TEST_API_URL = "http://127.0.0.1:8000"
    TEST_ACCESS_TOKEN = "mock_token_supervisor_123456"
    TEST_USER_ROLE = "SUPERVISOR"
    
    print("=== 主管大屏测试 ===")
    print(f"API地址: {TEST_API_URL}")
    print(f"用户角色: {TEST_USER_ROLE}")
    
    # 检查环境
    if not PYQT_AVAILABLE:
        print("❌ PyQt6不可用，无法运行GUI测试")
        print("请安装: pip install PyQt6")
        sys.exit(1)
    
    # 启动大屏
    print("正在启动主管大屏...")
    launch_supervisor_dashboard(TEST_API_URL, TEST_ACCESS_TOKEN, TEST_USER_ROLE)