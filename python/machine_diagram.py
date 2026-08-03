from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QPushButton, QSizePolicy, QWidget


class ParameterButton(QPushButton):
    selected = Signal(str)

    def __init__(self, key: str, code: str, label: str, color: str, symbol: str, parent: QWidget) -> None:
        super().__init__(f"{code}\n{label}", parent)
        self.key = key
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(self._icon(color, symbol))
        self.setIconSize(QSize(26, 26))
        self.setStyleSheet(
            f"QPushButton{{background:white;border:1px solid #dce3ec;"
            f"border-left:4px solid {color};border-radius:9px;padding:4px 7px;"
            "text-align:left;font:600 10px 'Segoe UI';color:#24324a;}"
            "QPushButton:hover{background:#f7faff;border-color:#9bbcf2;}"
        )
        self.clicked.connect(lambda: self.selected.emit(self.key))

    @staticmethod
    def _icon(color: str, symbol: str) -> QIcon:
        pixmap = QPixmap(28, 28)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(1, 1, 26, 26, 7, 7)
        painter.setPen(QColor("white"))
        font = QFont("Segoe UI Symbol", 12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, symbol)
        painter.end()
        return QIcon(pixmap)


class MachineDiagram(QWidget):
    parameter_selected = Signal(str)

    def __init__(self, parameters: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.parameters = parameters
        self.buttons: dict[str, ParameterButton] = {}
        self.setMinimumSize(820, 650)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        for key, p in parameters.items():
            button = ParameterButton(key, p.code, p.label, p.color, p.symbol, self)
            button.setToolTip(f"{p.label} ({p.unit})" if p.unit else p.label)
            button.selected.connect(self.parameter_selected)
            self.buttons[key] = button
        self._layout_buttons()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._layout_buttons()

    def _layout_buttons(self) -> None:
        w, h = self.width(), self.height()
        self.buttons["Fc"].setGeometry(18, 14, 150, 58)
        self.buttons["U"].setGeometry(max(410, w - 318), 14, 142, 58)
        self.buttons["I"].setGeometry(max(560, w - 166), 14, 142, 58)
        self.buttons["Er"].setGeometry(24, h - 190, 158, 58)
        self.buttons["theta_red"].setGeometry(max(590, w - 182), h - 190, 158, 58)

        keys = ["formula", "t", "Fr", "Dch", "Vch", "theta_m", "omega_m", "omega_red"]
        gap = 8
        margin = 16
        available = max(640, w - 2 * margin)
        button_w = (available - 3 * gap) // 4
        button_h = 58
        first_y = h - 122
        for index, key in enumerate(keys):
            row, col = divmod(index, 4)
            x = margin + col * (button_w + gap)
            y = first_y + row * (button_h + 6)
            self.buttons[key].setGeometry(x, y, button_w, button_h)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#fbfcfe"))

        top = 90
        bottom = self.height() - 215
        left = 36
        right = self.width() - 36
        machine_rect = QRect(left, top, right - left, max(300, bottom - top))

        painter.setPen(QPen(QColor("#d8e0ea"), 1))
        painter.setBrush(QColor("#eef2f7"))
        painter.drawRoundedRect(machine_rect, 18, 18)

        bx = machine_rect.x() + 42
        by = machine_rect.y() + 118
        bw = machine_rect.width() - 84
        bh = machine_rect.height() - 150
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#20242a"))
        painter.drawRoundedRect(QRect(bx, by, bw, bh), 7, 7)
        painter.setBrush(QColor("#595d62"))
        painter.drawRect(bx + 18, by + 18, bw - 36, 15)
        painter.drawRect(bx + 18, by + 55, bw - 36, 8)
        painter.drawRect(bx + 18, by + bh - 34, bw - 36, 18)

        painter.setBrush(QColor("#70c8c7"))
        painter.drawRoundedRect(QRect(bx + 8, by + 42, bw - 16, 20), 8, 8)
        painter.setPen(QPen(QColor("#b7f2ef"), 2))
        painter.drawLine(bx + 12, by + 45, bx + bw - 12, by + 45)

        cx = machine_rect.center().x() - 70
        cy = machine_rect.y() + 72
        painter.setPen(QPen(QColor("#ba6268"), 1))
        painter.setBrush(QColor("#ed8b91"))
        painter.drawRoundedRect(QRect(cx, cy, 140, 158), 10, 10)
        painter.setBrush(QColor("#db7079"))
        painter.drawRoundedRect(QRect(cx - 18, by + 35, 176, 34), 8, 8)
        painter.setBrush(QColor("#ed8b91"))
        painter.drawRoundedRect(QRect(cx + 10, by + 64, 120, 95), 8, 8)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("white"))
        painter.drawEllipse(QRect(cx + 28, cy + 28, 28, 28))
        painter.drawEllipse(QRect(cx + 84, cy + 28, 28, 28))

        painter.setBrush(QColor("#9ca3af"))
        painter.drawRoundedRect(QRect(cx + 48, by + 152, 44, 72), 6, 6)

        spring_y = by + 154
        spring_x = cx + 8
        painter.setPen(QPen(QColor("#8a6c2d"), 3))
        for i in range(14):
            x = spring_x + i * 9
            painter.drawLine(x, spring_y, x + 4, spring_y - 24)
            painter.drawLine(x + 4, spring_y - 24, x + 9, spring_y)
        painter.setPen(QPen(QColor("#c5a451"), 2))
        painter.drawLine(spring_x - 4, spring_y + 2, spring_x + 132, spring_y + 2)

        px = bx + bw - 86
        py = by + 88
        painter.setPen(QPen(QColor("#3d4652"), 3))
        painter.setBrush(QColor("#eef2f7"))
        painter.drawEllipse(QRect(px, py, 54, 54))
        painter.setBrush(QColor("#d1d8e2"))
        painter.drawEllipse(QRect(px + 18, py + 18, 18, 18))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#d7dce3"))
        for sx, sy in [
            (bx + 18, by + bh - 68), (bx + 18, by + bh - 48),
            (bx + bw - 18, by + 92), (bx + bw - 18, by + 126),
        ]:
            painter.drawEllipse(QRect(sx, sy, 8, 8))

        painter.setPen(QPen(QColor("#6b7280"), 2))
        painter.drawLine(left + 90, top + 56, cx - 15, cy - 8)
        painter.drawLine(cx + 140, cy - 8, right - 120, top + 50)

        painter.setPen(QPen(QColor("#2563eb"), 2))
        painter.drawLine(95, 72, bx + 48, by - 18)
        painter.drawLine(110, self.height() - 190, cx - 10, spring_y - 5)
        painter.drawLine(self.width() - 105, self.height() - 190, px + 27, py + 27)
