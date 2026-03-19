#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AHDUNYI 审核客户端启动器
支持动态配置文件加载，为 .exe 打包准备
启动流程：环境自检 -> 登录窗口 -> 主界面
"""

import os
import sys
import logging
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from client_config import get_config, create_example_config
from utils.room_monitor import create_room_monitor
# supervisor_dashboard 按需导入，避免顶层导入崩溃


def setup_logging(config):
    """配置日志系统"""
    log_level = getattr(logging, config.logging.level.upper(), logging.INFO)

    log_dir = Path(config.paths.logs_directory)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / config.logging.file

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler() if config.debug.enable_console else logging.NullHandler(),
        ]
    )
    return logging.getLogger(__name__)


def check_dependencies():
    """检查依赖（大小写不敏感）"""
    dependencies = [
        ('psutil',       ['psutil']),
        ('uiautomation', ['uiautomation']),
        ('PyQt6',        ['PyQt6', 'PyQt6.QtWidgets']),
        ('requests',     ['requests']),
    ]
    missing = []
    for display_name, import_names in dependencies:
        found = False
        for import_name in import_names:
            try:
                __import__(import_name)
                print(f"[OK] {display_name}")
                found = True
                break
            except ImportError:
                pass
        if not found:
            missing.append(display_name)
            print(f"[MISS] {display_name}")
    return missing


def start_room_monitor(config, logger):
    """启动RoomMonitor探针（后台守护线程）"""
    try:
        from utils.room_monitor import create_room_monitor
        room_monitor = create_room_monitor(
            target_process=config.room_monitor.target_process,
            heartbeat_interval=config.room_monitor.heartbeat_interval,
            max_depth=config.room_monitor.max_search_depth,
            room_id_pattern=config.room_monitor.room_id_pattern,
        )
        if room_monitor:
            room_monitor.start()   # 内部已 daemon=True，主线程退出时自动销毁
            logger.info(f"RoomMonitor 已启动，监控: {config.room_monitor.target_process}")
            return room_monitor
        else:
            logger.warning("RoomMonitor 创建失败（可能不支持当前系统）")
            return None
    except Exception as e:
        logger.error(f"启动 RoomMonitor 失败: {e}")
        return None


def start_gui(config, logger):
    """
    启动 GUI 事件循环。

    流程：
      1. 创建 QApplication
      2. 显示登录窗口
      3. 登录成功 -> 显示主监控窗口（当前为占位 Dashboard）
      4. app.exec() 阻塞主线程直到所有窗口关闭
    """
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
    from PyQt6.QtCore import Qt, QTimer

    app = QApplication(sys.argv)
    app.setApplicationName("AHDUNYI 审核客户端")
    app.setOrganizationName("AHDUNYI")

    # 全局暗色调色板
    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor("#0f1117"))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor("#e2e8f0"))
    palette.setColor(QPalette.ColorRole.Base,            QColor("#1a1d2e"))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor("#252842"))
    palette.setColor(QPalette.ColorRole.Text,            QColor("#e2e8f0"))
    palette.setColor(QPalette.ColorRole.Button,          QColor("#1a1d2e"))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor("#e2e8f0"))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor("#4f8ef7"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    # ----------------------------------------------------------------
    # 主监控窗口（登录成功后显示）
    # ----------------------------------------------------------------
    def build_main_window(token_info: dict) -> QMainWindow:
        """构建登录后的主界面"""
        role     = token_info.get('role', 'UNKNOWN')
        username = token_info.get('username', '用户')
        token    = token_info.get('access_token', '')

        # 如果是主管，尝试加载 SupervisorDashboard
        if role == 'SUPERVISOR':
            try:
                from app.ui.supervisor_dashboard import SupervisorDashboard
                win = SupervisorDashboard(config.server.url, token)
                win.setWindowTitle(f"AHDUNYI 主管大屏 — {username}")
                return win
            except Exception as e:
                logger.warning(f"主管大屏加载失败，降级到普通主界面: {e}")

        # 普通审核员 / 组长 主界面（占位，后续可扩展）
        win = QMainWindow()
        win.setWindowTitle(f"AHDUNYI 审核客户端 — {username} ({role})")
        win.setGeometry(100, 100,
                        config.gui.window_width,
                        config.gui.window_height)
        win.setStyleSheet("background-color: #0f1117;")

        central = QWidget()
        win.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_welcome = QLabel(f"欢迎，{username}")
        lbl_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_welcome.setStyleSheet(
            "color: #e2e8f0; font-size: 26px; font-weight: 700; margin-bottom: 12px;"
        )
        layout.addWidget(lbl_welcome)

        lbl_role = QLabel(f"角色: {role}  |  服务器: {config.server.url}")
        lbl_role.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_role.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(lbl_role)

        lbl_hint = QLabel("主界面开发中，当前已完成登录验证")
        lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_hint.setStyleSheet(
            "color: #4ade80; font-size: 14px; margin-top: 24px;"
        )
        layout.addWidget(lbl_hint)

        return win

    # ----------------------------------------------------------------
    # 登录窗口
    # ----------------------------------------------------------------
    try:
        from app.ui.login_window import LoginWindow
    except ImportError as e:
        logger.error(f"无法导入 LoginWindow: {e}")
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "启动失败", f"LoginWindow 模块加载失败:\n{e}")
        return 1

    main_window_ref = []   # 用列表持有引用，防止被 GC 回收

    login_win = LoginWindow(server_url=config.server.url)

    def on_login_success(token_info: dict):
        """登录成功回调：隐藏登录窗口，显示主界面"""
        login_win.hide()
        try:
            main_win = build_main_window(token_info)
            main_window_ref.append(main_win)
            main_win.show()
            logger.info("主界面已显示")
        except Exception as e:
            logger.error(f"打开主界面失败: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None, "打开主界面失败",
                f"无法打开主界面:\n{str(e)}"
            )
            login_win.show()   # 登录失败则重新显示登录窗口

    login_win.login_success.connect(on_login_success)
    login_win.show()
    logger.info("登录窗口已显示")

    return app.exec()


def main():
    """主函数（返回退出代码）"""
    print("=" * 60)
    print("AHDUNYI 审核客户端启动器")
    print("=" * 60)

    # 1. 加载配置
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    from client_config import ConfigManager
    config = ConfigManager(config_file).load()

    print(f"[ENV ] {config.display_name}")
    print(f"[SRV ] {config.server.url}")
    print(f"[PROC] {config.room_monitor.target_process}")
    print(f"[DATA] {config.paths.data_directory}")

    # 2. 检查依赖
    print("\n[*] 依赖检查:")
    missing = check_dependencies()
    if missing:
        print(f"[ERR] 缺少依赖: {', '.join(missing)}")
        print("请运行: pip install " + " ".join(missing))
        if not config.debug.enable_console:
            input("按 Enter 退出...")
        sys.exit(1)

    # 3. 配置日志
    logger = setup_logging(config)

    # 4. 启动后台 RoomMonitor 守护线程
    print("\n[*] 启动后台服务:")
    room_monitor = None
    if config.features.auto_start_monitor:
        room_monitor = start_room_monitor(config, logger)
        if room_monitor:
            print("[OK] RoomMonitor 已启动")

    # 5. 启动 GUI（主线程事件循环，阻塞至所有窗口关闭）
    print("\n[*] 启动 GUI...")
    exit_code = start_gui(config, logger)

    # 6. 清理
    print("\n[*] 清理资源...")
    if room_monitor:
        room_monitor.stop()
        logger.info("RoomMonitor 已停止")
    logger.info("客户端已关闭")
    print("[OK] 客户端已安全关闭")

    return exit_code


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h'):
        print("用法: python client_launcher.py [配置文件路径]")
        sys.exit(0)

    elif len(sys.argv) > 1 and sys.argv[1] == '--create-example':
        create_example_config()
        print("[OK] 示例配置文件已创建: config.example.json")
        sys.exit(0)

    elif len(sys.argv) > 1 and sys.argv[1] == '--check-deps':
        print("[*] 检查依赖:")
        missing = check_dependencies()
        sys.exit(1 if missing else 0)

    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n[ERR] 致命错误: {e}")
        import traceback
        traceback.print_exc()
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(
                None, "AHDUNYI - 致命错误",
                f"程序遇到致命错误:\n\n{str(e)}\n\n请检查日志文件。"
            )
        except Exception:
            pass
        input("\n按 Enter 退出...")
        sys.exit(1)
