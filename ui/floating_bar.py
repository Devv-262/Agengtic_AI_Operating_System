"""
ui/floating_bar.py
-------------------
Role: A Spotlight/Raycast-style floating search bar for the Agentic-AI-OS.
Lives in the system tray, pops up centered near the top of the screen on a
global hotkey (default: Ctrl+Space), and sends whatever you type to
OSAgentSystem, showing the response inline.

Command processing runs on a worker thread so the UI never freezes while the
agent is thinking/calling tools. Destructive-tool confirmation prompts are
routed through a Qt dialog on the main thread instead of stdin (see
tools/_confirm.py).
"""
import sys

from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon, QFont, QAction, QGuiApplication, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLineEdit, QTextEdit, QVBoxLayout,
    QSystemTrayIcon, QMenu, QMessageBox, QGraphicsDropShadowEffect,
)

from src.agent import OSAgentSystem
from src.logging_config import setup_logging
from tools._confirm import set_confirm_handler

HOTKEY = "ctrl+space"

STYLE = """
#Container {
    background-color: rgba(24, 24, 28, 235);
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 30);
}
QLineEdit {
    background: transparent;
    border: none;
    color: #f2f2f2;
    font-size: 18px;
    padding: 6px 4px;
}
QTextEdit {
    background: transparent;
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 20);
    color: #cfcfcf;
    font-size: 14px;
    padding: 10px 4px 4px 4px;
}
"""


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
        box.setWindowTitle("Agentic-AI-OS — Confirm Action")
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
# Worker: runs OSAgentSystem.process_command off the UI thread.
# ---------------------------------------------------------------------------
class AgentWorker(QThread):
    finished_with_result = pyqtSignal(str)

    def __init__(self, agent: OSAgentSystem, command: str):
        super().__init__()
        self.agent = agent
        self.command = command

    def run(self) -> None:
        response = self.agent.process_command(self.command)
        self.finished_with_result.emit(response)


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
        self.setFixedWidth(640)
        self.setStyleSheet(STYLE)
        self.setObjectName("Root")

        container = QWidget(self)
        container.setObjectName("Container")

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 160))
        container.setGraphicsEffect(shadow)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask Agentic-AI-OS anything…")
        self.input.setFont(QFont("Segoe UI", 12))
        self.input.returnPressed.connect(self._submit)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Segoe UI", 10))
        self.output.hide()
        self.output.setMaximumHeight(280)

        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(16, 12, 16, 12)
        inner_layout.setSpacing(0)
        inner_layout.addWidget(self.input)
        inner_layout.addWidget(self.output)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(container)

    def _position_top_center(self) -> None:
        screen = QGuiApplication.primaryScreen().geometry()
        x = screen.center().x() - self.width() // 2
        y = screen.top() + int(screen.height() * 0.18)
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
        self.output.show()
        self.output.setPlainText("Thinking…")
        self.adjustSize()

        self.worker = AgentWorker(self.agent, text)
        self.worker.finished_with_result.connect(self._on_result)
        self.worker.start()

    def _on_result(self, response: str) -> None:
        self.output.setPlainText(response)
        self.input.setEnabled(True)
        self.input.clear()
        self.input.setFocus()

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)


def _make_tray_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#5b8def"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, 56, 56)
    painter.end()
    return QIcon(pixmap)


def _register_hotkey(bar: FloatingBar) -> None:
    try:
        import keyboard
    except ImportError:
        print(
            "[WARN] 'keyboard' package not installed — global hotkey disabled. "
            "Install it with: pip install keyboard"
        )
        return

    # keyboard's callback runs on its own background thread; emit a Qt signal
    # (queued automatically across threads) instead of touching widgets directly.
    keyboard.add_hotkey(HOTKEY, bar.toggle_visibility.emit)


def main() -> None:
    setup_logging()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    print("Initialising agent…")
    agent = OSAgentSystem()

    bridge = ConfirmBridge()
    set_confirm_handler(bridge.confirm)

    bar = FloatingBar(agent)
    _register_hotkey(bar)

    tray = QSystemTrayIcon(_make_tray_icon(), app)
    tray.setToolTip(f"Agentic-AI-OS — press {HOTKEY} to open")

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

    print(f"Agentic-AI-OS running in the system tray. Press {HOTKEY} to open the bar.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
