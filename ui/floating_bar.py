"""
ui/floating_bar.py
-------------------
Role: A Spotlight/Raycast-style floating command bar for the Agentic-AI-OS.
Lives in the system tray, pops up centered near the top of the screen on a
global hotkey (Ctrl+Space or Ctrl+Shift), and sends whatever you type to
OSAgentSystem — showing a live, timestamped activity log of every tool call
the agent makes, followed by its final answer.

Command processing runs on a worker thread so the UI never freezes while the
agent is thinking/calling tools. Destructive-tool confirmation prompts are
routed through a Qt dialog on the main thread instead of stdin (see
tools/_confirm.py).
"""
import os
import sys
from datetime import datetime

from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon, QFont, QAction, QGuiApplication, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout,
    QSystemTrayIcon, QMenu, QMessageBox, QGraphicsDropShadowEffect,
)

from src.agent import OSAgentSystem
from src.logging_config import setup_logging
from tools._confirm import set_confirm_handler

HOTKEYS = ["ctrl+space", "ctrl+shift"]

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
ICON_PNG = os.path.join(ASSETS_DIR, "icon.png")

APP_NAME = "Agentic AI OS"

# Futuristic dark-tech palette, matching assets/icon.png (navy -> indigo -> cyan).
COLOR_BG = "rgba(10, 12, 22, 235)"
COLOR_BORDER = "rgba(255, 255, 255, 25)"
COLOR_TEXT = "#eef2ff"
COLOR_MUTED = "#8b93b8"
COLOR_ACCENT = "#67e8f9"    # cyan
COLOR_ACCENT2 = "#818cf8"   # indigo
COLOR_ERROR = "#f87171"
COLOR_OK = "#4ade80"

STYLE = f"""
#Container {{
    background-color: {COLOR_BG};
    border-radius: 16px;
    border: 1px solid {COLOR_BORDER};
}}
#Title {{
    color: {COLOR_TEXT};
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
#StatusText {{
    color: {COLOR_MUTED};
    font-size: 11px;
}}
QLineEdit {{
    background: rgba(255, 255, 255, 12);
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    color: {COLOR_TEXT};
    font-size: 17px;
    padding: 10px 12px;
}}
QLineEdit:focus {{
    border: 1px solid {COLOR_ACCENT};
}}
#ActivityLog {{
    background: rgba(255, 255, 255, 6);
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    color: {COLOR_MUTED};
    font-family: Consolas, "Cascadia Code", monospace;
    font-size: 11px;
    padding: 8px;
}}
#Response {{
    background: transparent;
    border: none;
    color: {COLOR_TEXT};
    font-size: 14px;
    padding: 6px 2px 2px 2px;
}}
"""


def _status_dot_style(color: str) -> str:
    return (
        f"background-color: {color}; border-radius: 5px; min-width: 10px; "
        f"max-width: 10px; min-height: 10px; max-height: 10px;"
    )


# ---------------------------------------------------------------------------
# Confirmation bridge: lets a background worker thread block on a Qt dialog
# that must run on the main/GUI thread.
# ---------------------------------------------------------------------------
class ConfirmBridge(QObject):
    ask_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.result = False
        self.ask_signal.connect(self._ask, Qt.ConnectionType.BlockingQueuedConnection)

    def _ask(self, description: str) -> None:
        box = QMessageBox()
        box.setWindowTitle(f"{APP_NAME} — Confirm Action")
        box.setText(description)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.result = box.exec() == QMessageBox.StandardButton.Yes

    def confirm(self, description: str) -> bool:
        self.ask_signal.emit(description)
        return self.result


# ---------------------------------------------------------------------------
# Worker: streams OSAgentSystem.stream_command off the UI thread, emitting
# one signal per step (for the activity log) and one final signal.
# ---------------------------------------------------------------------------
class AgentWorker(QThread):
    log_event = pyqtSignal(dict)
    finished_with_result = pyqtSignal(str, bool)  # (text, is_error)

    def __init__(self, agent: OSAgentSystem, command: str):
        super().__init__()
        self.agent = agent
        self.command = command

    def run(self) -> None:
        final_text = None
        is_error = False
        for event in self.agent.stream_command(self.command):
            self.log_event.emit(event)
            if event["type"] == "final":
                final_text = event["content"]
            elif event["type"] == "error":
                final_text = f"Error: {event['message']}"
                is_error = True
        self.finished_with_result.emit(final_text or "(no response)", is_error)


# ---------------------------------------------------------------------------
# Main floating window
# ---------------------------------------------------------------------------
class FloatingBar(QWidget):
    toggle_visibility = pyqtSignal()

    def __init__(self, agent: OSAgentSystem):
        super().__init__()
        self.agent = agent
        self.worker = None
        self._build_ui()
        self.toggle_visibility.connect(self._toggle)

    def _build_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(680)
        self.setStyleSheet(STYLE)
        self.setObjectName("Root")
        if os.path.exists(ICON_PNG):
            self.setWindowIcon(QIcon(ICON_PNG))

        container = QWidget(self)
        container.setObjectName("Container")

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 10)
        shadow.setColor(Qt.GlobalColor.black)
        container.setGraphicsEffect(shadow)

        # --- Header: logo + title + status dot/text -------------------
        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 2, 8)

        logo = QLabel()
        if os.path.exists(ICON_PNG):
            logo.setPixmap(QPixmap(ICON_PNG).scaled(
                22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        header.addWidget(logo)

        title = QLabel(APP_NAME.upper())
        title.setObjectName("Title")
        header.addWidget(title)
        header.addStretch()

        self.status_dot = QLabel()
        self.status_dot.setStyleSheet(_status_dot_style(COLOR_MUTED))
        self.status_text = QLabel("Idle")
        self.status_text.setObjectName("StatusText")
        header.addWidget(self.status_text)
        header.addWidget(self.status_dot)

        # --- Input ------------------------------------------------------
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask Agentic-AI-OS anything…")
        self.input.setFont(QFont("Segoe UI", 12))
        self.input.returnPressed.connect(self._submit)

        # --- Live activity log (what the agent is doing, step by step) --
        self.activity_log = QTextEdit()
        self.activity_log.setObjectName("ActivityLog")
        self.activity_log.setReadOnly(True)
        self.activity_log.hide()
        self.activity_log.setFixedHeight(120)

        # --- Final response ----------------------------------------------
        self.response = QTextEdit()
        self.response.setObjectName("Response")
        self.response.setReadOnly(True)
        self.response.hide()
        self.response.setMaximumHeight(200)

        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(18, 14, 18, 16)
        inner_layout.setSpacing(10)
        inner_layout.addLayout(header)
        inner_layout.addWidget(self.input)
        inner_layout.addWidget(self.activity_log)
        inner_layout.addWidget(self.response)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(container)

    def _set_status(self, text: str, color: str) -> None:
        self.status_text.setText(text)
        self.status_dot.setStyleSheet(_status_dot_style(color))

    def _position_top_center(self) -> None:
        screen = QGuiApplication.primaryScreen().geometry()
        x = screen.center().x() - self.width() // 2
        y = screen.top() + int(screen.height() * 0.15)
        self.move(QPoint(x, y))

    def _toggle(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self._position_top_center()
            self.show()
            self.raise_()
            self.activateWindow()
            self.input.setFocus()

    def _submit(self) -> None:
        text = self.input.text().strip()
        if not text:
            return

        self.input.setEnabled(False)
        self.activity_log.clear()
        self.activity_log.show()
        self.response.hide()
        self._set_status("Working…", COLOR_ACCENT2)
        self.adjustSize()

        self.worker = AgentWorker(self.agent, text)
        self.worker.log_event.connect(self._on_log_event)
        self.worker.finished_with_result.connect(self._on_result)
        self.worker.start()

    def _append_log(self, html_line: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append(f'<span style="color:{COLOR_MUTED}">[{timestamp}]</span> {html_line}')
        self.activity_log.verticalScrollBar().setValue(self.activity_log.verticalScrollBar().maximum())

    def _on_log_event(self, event: dict) -> None:
        etype = event["type"]
        if etype == "tool_call":
            args = ", ".join(f"{k}={v!r}" for k, v in event["args"].items())
            args = (args[:120] + "…") if len(args) > 120 else args
            self._append_log(f'<span style="color:{COLOR_ACCENT}">→ calling</span> <b>{event["name"]}</b>({args})')
        elif etype == "tool_result":
            result = event["result"].replace("\n", " ")
            result = (result[:160] + "…") if len(result) > 160 else result
            self._append_log(f'<span style="color:{COLOR_MUTED}">← {event["name"]} returned:</span> {result}')
        elif etype == "error":
            self._append_log(f'<span style="color:{COLOR_ERROR}">✕ error:</span> {event["message"]}')

    def _on_result(self, response_text: str, is_error: bool) -> None:
        self._set_status("Error" if is_error else "Done", COLOR_ERROR if is_error else COLOR_OK)
        self._append_log(
            f'<span style="color:{COLOR_ERROR if is_error else COLOR_OK}">'
            f'{"✕ failed" if is_error else "✓ done"}</span>'
        )
        self.response.setPlainText(response_text)
        self.response.show()
        self.input.setEnabled(True)
        self.input.clear()
        self.input.setFocus()
        self.adjustSize()

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)


def _load_icon() -> QIcon:
    if os.path.exists(ICON_PNG):
        return QIcon(ICON_PNG)
    # Fallback: solid circle, in case assets/icon.png hasn't been generated
    # yet (run scripts/generate_icon.py to create it).
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    return QIcon(pixmap)


def _register_hotkeys(bar: FloatingBar) -> list:
    try:
        import keyboard
    except ImportError:
        print(
            "[WARN] 'keyboard' package not installed — global hotkeys disabled. "
            "Install it with: pip install keyboard"
        )
        return []

    registered = []
    for hotkey in HOTKEYS:
        try:
            # keyboard's callback runs on its own background thread; emit a
            # Qt signal (queued automatically across threads) instead of
            # touching widgets directly.
            keyboard.add_hotkey(hotkey, bar.toggle_visibility.emit)
            registered.append(hotkey)
        except Exception as e:
            print(f"[WARN] Failed to register hotkey '{hotkey}': {e}")
    return registered


def main() -> None:
    setup_logging()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app_icon = _load_icon()
    app.setWindowIcon(app_icon)

    print("Initialising agent…")
    agent = OSAgentSystem()

    bridge = ConfirmBridge()
    set_confirm_handler(bridge.confirm)

    bar = FloatingBar(agent)
    registered_hotkeys = _register_hotkeys(bar)

    tray = QSystemTrayIcon(app_icon, app)
    hotkey_label = " or ".join(h.title().replace("Ctrl", "Ctrl") for h in registered_hotkeys) or "(no hotkey registered)"
    tray.setToolTip(f"{APP_NAME} — press {hotkey_label} to open")

    menu = QMenu()
    show_action = QAction("Show")
    show_action.triggered.connect(bar.toggle_visibility.emit)
    quit_action = QAction("Quit")
    quit_action.triggered.connect(app.quit)
    menu.addAction(show_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: bar.toggle_visibility.emit()
        if reason == QSystemTrayIcon.ActivationReason.Trigger
        else None
    )
    tray.show()

    print(f"{APP_NAME} running in the system tray. Hotkeys: {hotkey_label}.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
