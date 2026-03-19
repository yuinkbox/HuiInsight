#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AHDUNYI 审核客户端 - 登录窗口
对接后端 /api/auth/login JWT 接口
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QMessageBox, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 后台登录线程 —— 避免网络请求阻塞 UI
# ---------------------------------------------------------------------------
class LoginThread(QThread):
    """在后台线程中完成 HTTP 登录请求。"""

    success = pyqtSignal(dict)   # 登录成功，携带 {access_token, role, username, ...}
    failure = pyqtSignal(str)    # 登录失败，携带错误消息

    def __init__(self, server_url: str, username: str, password: str):
        super().__init__()
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.password = password

    def run(self):
        try:
            import requests
            resp = requests.post(
                f"{self.server_url}/api/auth/login",
                json={"username": self.username, "password": self.password},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.success.emit(data)
            elif resp.status_code == 401:
                self.failure.emit("用户名或密码错误")
            elif resp.status_code == 403:
                self.failure.emit("账号已被禁用，请联系管理员")
            else:
                self.failure.emit(f"服务器错误 ({resp.status_code})")
        except requests.exceptions.ConnectionError:
            self.failure.emit(f"无法连接服务器\n{self.server_url}\n请检查网络或服务器状态")
        except requests.exceptions.Timeout:
            self.failure.emit("登录请求超时（10s），请稍后重试")
        except Exception as e:
            self.failure.emit(f"登录异常: {str(e)}")


# ---------------------------------------------------------------------------
# 登录窗口
# ---------------------------------------------------------------------------
class LoginWindow(QWidget):
    """
    登录窗口。

    登录成功后发出 login_success(token_info: dict) 信号，
    由调用方决定如何跳转到主界面。
    """

    login_success = pyqtSignal(dict)   # {access_token, role, username, ...}

    _DARK_BG   = "#0f1117"
    _CARD_BG   = "#1a1d2e"
    _ACCENT    = "#4f8ef7"
    _ACCENT_HV = "#6ba3ff"
    _TEXT      = "#e2e8f0"
    _MUTED     = "#64748b"
    _BORDER    = "#2d3250"
    _ERROR     = "#f87171"
    _SUCCESS   = "#4ade80"

    def __init__(self, server_url: str, parent=None):
        super().__init__(parent)
        self.server_url = server_url
        self._login_thread: Optional[LoginThread] = None
        self._setup_window()
        self._setup_ui()
        self._apply_styles()

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------
    def _setup_window(self):
        self.setWindowTitle("AHDUNYI 审核客户端 — 登录")
        self.setFixedSize(420, 520)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        # 居中显示
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width()  - self.width())  // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 外层背景容器
        outer = QWidget()
        outer.setObjectName("outer")
        root.addWidget(outer)

        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(40, 48, 40, 40)
        outer_layout.setSpacing(0)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Logo / 品牌区
        brand_label = QLabel("AHDUNYI")
        brand_label.setObjectName("brand")
        brand_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(brand_label)

        sub_label = QLabel("审核管理系统")
        sub_label.setObjectName("sub")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(sub_label)

        outer_layout.addSpacing(36)

        # ── 卡片
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(16)
        outer_layout.addWidget(card)

        # 标题
        title = QLabel("登录你的账号")
        title.setObjectName("card_title")
        card_layout.addWidget(title)

        card_layout.addSpacing(4)

        # 用户名
        self._lbl_user = QLabel("用户名")
        self._lbl_user.setObjectName("field_label")
        card_layout.addWidget(self._lbl_user)

        self._input_user = QLineEdit()
        self._input_user.setObjectName("field_input")
        self._input_user.setPlaceholderText("请输入用户名")
        self._input_user.returnPressed.connect(self._on_login_clicked)
        card_layout.addWidget(self._input_user)

        # 密码
        self._lbl_pass = QLabel("密码")
        self._lbl_pass.setObjectName("field_label")
        card_layout.addWidget(self._lbl_pass)

        self._input_pass = QLineEdit()
        self._input_pass.setObjectName("field_input")
        self._input_pass.setPlaceholderText("请输入密码")
        self._input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._input_pass.returnPressed.connect(self._on_login_clicked)
        card_layout.addWidget(self._input_pass)

        card_layout.addSpacing(8)

        # 登录按钮
        self._btn_login = QPushButton("登 录")
        self._btn_login.setObjectName("btn_login")
        self._btn_login.setFixedHeight(44)
        self._btn_login.clicked.connect(self._on_login_clicked)
        card_layout.addWidget(self._btn_login)

        # 状态提示
        self._status_label = QLabel("")
        self._status_label.setObjectName("status_label")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        self._status_label.hide()
        card_layout.addWidget(self._status_label)

        outer_layout.addStretch()

        # ── 底部服务器信息
        server_info = QLabel(f"服务器: {self.server_url}")
        server_info.setObjectName("server_info")
        server_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(server_info)

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------
    def _apply_styles(self):
        self.setStyleSheet(f"""
            /* 窗口背景 */
            QWidget#outer {{
                background-color: {self._DARK_BG};
            }}
            LoginWindow {{
                background-color: {self._DARK_BG};
            }}

            /* 品牌字 */
            QLabel#brand {{
                color: {self._ACCENT};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 32px;
                font-weight: 800;
                letter-spacing: 6px;
            }}
            QLabel#sub {{
                color: {self._MUTED};
                font-size: 13px;
                letter-spacing: 2px;
            }}

            /* 卡片 */
            QFrame#card {{
                background-color: {self._CARD_BG};
                border: 1px solid {self._BORDER};
                border-radius: 12px;
            }}
            QLabel#card_title {{
                color: {self._TEXT};
                font-size: 17px;
                font-weight: 600;
            }}

            /* 输入框标签 */
            QLabel#field_label {{
                color: {self._MUTED};
                font-size: 12px;
                font-weight: 500;
            }}

            /* 输入框 */
            QLineEdit#field_input {{
                background-color: #252842;
                color: {self._TEXT};
                border: 1px solid {self._BORDER};
                border-radius: 7px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QLineEdit#field_input:focus {{
                border: 1px solid {self._ACCENT};
            }}
            QLineEdit#field_input::placeholder {{
                color: {self._MUTED};
            }}

            /* 登录按钮 */
            QPushButton#btn_login {{
                background-color: {self._ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 2px;
            }}
            QPushButton#btn_login:hover {{
                background-color: {self._ACCENT_HV};
            }}
            QPushButton#btn_login:pressed {{
                background-color: #3a6fd8;
            }}
            QPushButton#btn_login:disabled {{
                background-color: #2d3250;
                color: {self._MUTED};
            }}

            /* 状态 */
            QLabel#status_label {{
                font-size: 13px;
                padding: 6px;
            }}

            /* 底部服务器信息 */
            QLabel#server_info {{
                color: {self._MUTED};
                font-size: 11px;
            }}
        """)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _on_login_clicked(self):
        username = self._input_user.text().strip()
        password = self._input_pass.text()

        if not username:
            self._show_error("请输入用户名")
            self._input_user.setFocus()
            return
        if not password:
            self._show_error("请输入密码")
            self._input_pass.setFocus()
            return

        self._set_loading(True)
        self._show_status("正在登录...", color=self._MUTED)

        self._login_thread = LoginThread(self.server_url, username, password)
        self._login_thread.success.connect(self._on_login_success)
        self._login_thread.failure.connect(self._on_login_failure)
        self._login_thread.start()

    def _on_login_success(self, token_info: dict):
        logger.info(f"登录成功: {token_info.get('username', '?')} / role={token_info.get('role', '?')}")
        self._show_status("登录成功，正在进入系统...", color=self._SUCCESS)
        self._set_loading(False)
        # 短暂显示成功提示后跳转
        QTimer.singleShot(600, lambda: self.login_success.emit(token_info))

    def _on_login_failure(self, error_msg: str):
        logger.warning(f"登录失败: {error_msg}")
        self._show_error(error_msg)
        self._set_loading(False)
        self._input_pass.clear()
        self._input_pass.setFocus()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _set_loading(self, loading: bool):
        self._btn_login.setEnabled(not loading)
        self._input_user.setEnabled(not loading)
        self._input_pass.setEnabled(not loading)
        self._btn_login.setText("登录中..." if loading else "登 录")

    def _show_status(self, msg: str, color: str):
        self._status_label.setText(msg)
        self._status_label.setStyleSheet(f"font-size: 13px; color: {color}; padding: 6px;")
        self._status_label.show()

    def _show_error(self, msg: str):
        self._show_status(msg, self._ERROR)
