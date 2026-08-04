from __future__ import annotations

import struct
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QLinearGradient, QPainter, QPen, QPixmap

PNG_NAME = "sp55_logo.png"
ICO_NAME = "sp55_logo.ico"


def _draw_logo(size: int = 256) -> QImage:
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    scale = size / 256.0
    painter.scale(scale, scale)

    background = QLinearGradient(0, 0, 0, 256)
    background.setColorAt(0.0, QColor("#4fb6ff"))
    background.setColorAt(0.48, QColor("#0874db"))
    background.setColorAt(1.0, QColor("#062d72"))
    painter.setPen(QPen(QColor("#07306f"), 2))
    painter.setBrush(background)
    painter.drawRoundedRect(QRectF(8, 8, 240, 240), 42, 42)

    # Cadre de raquette et cordage.
    painter.setBrush(QColor("#0b3b86"))
    painter.setPen(QPen(QColor("white"), 8))
    painter.drawEllipse(QRectF(42, 42, 174, 112))
    painter.setPen(QPen(QColor("#9ed8ff"), 2))
    for x in range(62, 208, 16):
        painter.drawLine(x, 55, x, 140)
    for y in range(60, 142, 14):
        painter.drawLine(55, y, 202, y)

    # Bloc de traction à gauche.
    painter.setPen(QPen(QColor("#072c66"), 3))
    painter.setBrush(QColor("#f5f9ff"))
    painter.drawRoundedRect(QRectF(18, 91, 77, 46), 8, 8)
    painter.setBrush(QColor("#22b8ff"))
    painter.drawRoundedRect(QRectF(29, 102, 35, 14), 3, 3)
    painter.setBrush(QColor("#d7e8fb"))
    painter.drawRect(QRectF(70, 102, 13, 6))
    painter.drawRect(QRectF(70, 112, 13, 6))
    painter.setBrush(QColor("#d8e7f7"))
    painter.drawRoundedRect(QRectF(87, 99, 34, 31), 6, 6)
    painter.setBrush(QColor("#0c4f9b"))
    painter.drawRoundedRect(QRectF(105, 111, 35, 9), 4, 4)

    # Deux pinces de maintien.
    for cx in (154, 187):
        painter.setPen(QPen(QColor("#062d72"), 3))
        painter.setBrush(QColor("#eef6ff"))
        painter.drawRoundedRect(QRectF(cx - 11, 83, 22, 50), 8, 8)
        painter.setBrush(QColor("#7eb9ef"))
        painter.drawEllipse(QRectF(cx - 9, 77, 18, 20))
        painter.setBrush(QColor("#dfeeff"))
        painter.drawRect(QRectF(cx - 5, 131, 10, 24))

    # Ligne de traction.
    painter.setPen(QPen(QColor("white"), 4))
    painter.drawLine(119, 115, 143, 103)

    # Marque SP55.
    painter.setFont(QFont("Segoe UI", 48, QFont.Bold, italic=True))
    painter.setPen(QColor("white"))
    painter.drawText(QRectF(30, 168, 115, 60), Qt.AlignCenter, "SP")
    painter.setPen(QColor("#8bd8ff"))
    painter.drawText(QRectF(125, 168, 105, 60), Qt.AlignCenter, "55")

    painter.end()
    return image


def _png_bytes(image: QImage) -> bytes:
    array = QByteArray()
    buffer = QBuffer(array)
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(array)


def _write_png_ico(path: Path, png_data: bytes, width: int, height: int) -> None:
    # Un fichier ICO moderne peut contenir directement une image PNG.
    icon_dir = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack(
        "<BBBBHHII",
        0 if width >= 256 else width,
        0 if height >= 256 else height,
        0,
        0,
        1,
        32,
        len(png_data),
        6 + 16,
    )
    path.write_bytes(icon_dir + entry + png_data)


def ensure_icon_files(directory: Path | None = None) -> tuple[Path, Path]:
    target = directory or Path(__file__).resolve().parent
    target.mkdir(parents=True, exist_ok=True)
    png_path = target / PNG_NAME
    ico_path = target / ICO_NAME
    image = _draw_logo(256)
    png_data = _png_bytes(image)
    if not png_path.exists():
        png_path.write_bytes(png_data)
    if not ico_path.exists():
        _write_png_ico(ico_path, png_data, 256, 256)
    return png_path, ico_path


def application_icon(directory: Path | None = None) -> QIcon:
    png_path, ico_path = ensure_icon_files(directory)
    icon = QIcon(str(ico_path))
    if icon.isNull():
        icon = QIcon(str(png_path))
    return icon


def logo_pixmap(size: int = 76, directory: Path | None = None) -> QPixmap:
    png_path, _ = ensure_icon_files(directory)
    return QPixmap(str(png_path)).scaled(
        size,
        size,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )
