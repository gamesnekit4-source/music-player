# -*- coding: utf-8 -*-

"""
MPlayer by Nikson
Полная версия

Зависимости:
python -m pip install PyQt5 pygame yt-dlp mutagen Pillow requests
"""

import os
import sys
import io
import json
import time
import random
import math
import shutil
import hashlib
import urllib.request
import ctypes
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QSlider,
    QListWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QAbstractItemView,
    QColorDialog,
    QComboBox,
    QSplitter,
    QFrame,
    QTabWidget,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QSizePolicy,
    QMenu,
    QAction,
    QLineEdit,
    QGraphicsDropShadowEffect,
)

from PyQt5.QtGui import (
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QBrush,
    QPen,
    QFont,
    QRegion,
    QMovie,
)

from PyQt5.QtCore import (
    Qt,
    QTimer,
    QThread,
    pyqtSignal,
    QRect,
)

import pygame


# ============================================================
# БИБЛИОТЕКИ
# ============================================================

try:
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except Exception:
    HAS_MUTAGEN = False

try:
    import yt_dlp
    HAS_YTDLP = True
except Exception:
    HAS_YTDLP = False


# ============================================================
# ПУТИ
# ============================================================

APP_NAME = "MPlayer by Nikson"

BASE_DIR = Path(
    os.path.dirname(
        os.path.abspath(sys.argv[0])
    )
)

DATA_DIR = BASE_DIR / "mplayer_data"
DATA_DIR.mkdir(exist_ok=True)

COVERS_DIR = DATA_DIR / "covers"
COVERS_DIR.mkdir(exist_ok=True)

ASSETS_DIR = DATA_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

PLAYLISTS_FILE = DATA_DIR / "playlists.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
THEMES_FILE = DATA_DIR / "themes.json"

ICON_PATH = str(BASE_DIR / "icon.ico")

DEFAULT_PLAYLIST = "Мой плейлист"


# ============================================================
# НАСТРОЙКИ
# ============================================================

DEFAULT_SETTINGS = {
    "theme": "dark",
    "accent": "#1db954",

    "font_family": "Segoe UI",
    "font_size": 13,

    "bg_mode": "color",
    "bg_color": "#0b0d10",
    "bg_image": "",
    "bg_darkness": 25,
    "bg_opacity": 100,

    "panel_opacity": 90,
    "playlist_opacity": 75,
    "track_opacity": 75,

    "cover_path": "",
    "cover_size": 220,
    "cover_radius": 18,

    "cover_shadow": "strong",

    "particles": "none",
    "particle_count": 80,
    "particle_speed": 45,
    "particle_size": 3,
    "particle_opacity": 80,
    "particle_color": "",

    "eq_preset": "Flat",
    "eq_bars": 18,
    "eq_speed": 55,
    "eq_style": "bars",
    "eq_color": "",

    "volume": 70,
    "bass": 0,
    "treble": 0,
    "balance": 0,
    "preamp": 0,

    "shuffle": False,
}


EQ_PRESETS = {
    "Flat": [0, 0, 0, 0, 0, 0, 0, 0],
    "Rock": [4, 3, 1, -1, 1, 3, 4, 4],
    "Pop": [-1, 2, 4, 4, 2, 0, -1, -2],
    "Jazz": [3, 2, 1, 1, 0, 1, 2, 3],
    "Classical": [4, 3, 2, 1, 0, 2, 3, 4],
    "Bass Boost": [7, 6, 4, 2, 0, 0, 0, 0],
    "Vocal": [-2, -1, 2, 4, 5, 4, 2, 0],
    "Electronic": [4, 3, 0, -2, 2, 4, 5, 3],
    "Custom": [0] * 8,
}


# ============================================================
# JSON
# ============================================================

def load_json(path, default):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print("Ошибка загрузки JSON:", e)

    return default


def save_json(path, data):
    try:
        tmp = path.with_suffix(path.suffix + ".tmp")

        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

        tmp.replace(path)

    except Exception as e:
        print("Ошибка сохранения:", e)


def load_settings():
    settings = dict(DEFAULT_SETTINGS)

    data = load_json(
        SETTINGS_FILE,
        {}
    )

    if isinstance(data, dict):
        settings.update(data)

    return settings


def save_settings(settings):
    save_json(
        SETTINGS_FILE,
        settings
    )


def load_themes():
    data = load_json(
        THEMES_FILE,
        {}
    )

    if not isinstance(data, dict):
        return {}

    return data


def save_themes(themes):
    save_json(
        THEMES_FILE,
        themes
    )


def load_playlists():
    default = {
        "playlists": {
            DEFAULT_PLAYLIST: []
        },
        "library": []
    }

    data = load_json(
        PLAYLISTS_FILE,
        default
    )

    if not isinstance(data, dict):
        return default

    data.setdefault(
        "playlists",
        {}
    )

    data.setdefault(
        "library",
        []
    )

    if not data["playlists"]:
        data["playlists"] = {
            DEFAULT_PLAYLIST: []
        }

    return data


def save_playlists(playlists, library):
    save_json(
        PLAYLISTS_FILE,
        {
            "playlists": playlists,
            "library": library
        }
    )


# ============================================================
# УТИЛИТЫ
# ============================================================

def fmt_time(seconds):
    try:
        seconds = max(
            0,
            int(seconds)
        )
    except Exception:
        seconds = 0

    minutes, sec = divmod(
        seconds,
        60
    )

    hours, minutes = divmod(
        minutes,
        60
    )

    if hours:
        return f"{hours}:{minutes:02d}:{sec:02d}"

    return f"{minutes}:{sec:02d}"


def duration_of(path):
    if not HAS_MUTAGEN:
        return 0.0

    try:
        audio = MutagenFile(path)

        if audio and audio.info:
            return float(
                audio.info.length
            )

    except Exception:
        pass

    return 0.0


def copy_asset(path, folder, prefix):
    if not path or not os.path.exists(path):
        return ""

    try:
        src = Path(path)

        digest = hashlib.sha1(
            str(src.resolve()).encode("utf-8")
        ).hexdigest()[:12]

        dst = (
            folder /
            f"{prefix}_{digest}{src.suffix.lower()}"
        )

        if not dst.exists():
            shutil.copy2(
                src,
                dst
            )

        return str(dst)

    except Exception:
        return ""


def rgba(hex_color, alpha):
    try:
        color = QColor(hex_color)
    except Exception:
        color = QColor("#000000")

    alpha = max(
        0,
        min(
            100,
            int(alpha)
        )
    )

    return (
        f"rgba("
        f"{color.red()},"
        f"{color.green()},"
        f"{color.blue()},"
        f"{round(255 * alpha / 100)}"
        f")"
    )


def is_gif(path):
    if not path:
        return False

    return str(path).lower().endswith(".gif")


# ============================================================
# WINDOWS TITLE BAR
# ============================================================

def rgb_to_colorref(hex_color):
    """
    Windows DWM использует формат COLORREF:
    0x00BBGGRR
    """

    color = QColor(hex_color)

    r = color.red()
    g = color.green()
    b = color.blue()

    return (
        r
        |
        (g << 8)
        |
        (b << 16)
    )


def set_windows_titlebar(window, settings):
    """
    Изменяет стандартную верхнюю панель Windows 10/11
    в соответствии с текущей темой MPlayer.

    Никакого FramelessWindowHint здесь нет,
    поэтому стандартные кнопки Windows:
    свернуть / развернуть / закрыть
    сохраняются.
    """

    if sys.platform != "win32":
        return

    try:
        hwnd = int(window.winId())

        dark = (
            settings.get(
                "theme",
                "dark"
            )
            == "dark"
        )

        if dark:
            caption = "#111318"
            text = "#F5F7FA"

        else:
            caption = "#F3F5F7"
            text = "#111318"

        caption_color = ctypes.c_int(
            rgb_to_colorref(caption)
        )

        text_color = ctypes.c_int(
            rgb_to_colorref(text)
        )

        # Windows 11 / современные версии DWM
        DWMWA_CAPTION_COLOR = 35
        DWMWA_TEXT_COLOR = 36

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            ctypes.c_uint(DWMWA_CAPTION_COLOR),
            ctypes.byref(caption_color),
            ctypes.sizeof(caption_color)
        )

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            ctypes.c_uint(DWMWA_TEXT_COLOR),
            ctypes.byref(text_color),
            ctypes.sizeof(text_color)
        )

    except Exception as e:
        print(
            "Не удалось изменить верхнюю панель Windows:",
            e
        )


# ============================================================
# SLIDER
# ============================================================

class ClickableSlider(QSlider):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dragging = False

    def set_from_x(self, x):
        groove = max(
            1,
            self.width() - 1
        )

        x = max(
            0,
            min(
                groove,
                int(x)
            )
        )

        ratio = x / groove

        value = (
            self.minimum()
            +
            ratio *
            (
                self.maximum()
                -
                self.minimum()
            )
        )

        self.setValue(
            int(round(value))
        )

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.LeftButton
            and
            self.orientation() == Qt.Horizontal
        ):
            self.dragging = True

            self.set_from_x(
                event.pos().x()
            )

            self.sliderPressed.emit()

            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self.dragging
            and
            self.orientation() == Qt.Horizontal
        ):
            self.set_from_x(
                event.pos().x()
            )

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            event.button() == Qt.LeftButton
            and
            self.dragging
        ):
            self.set_from_x(
                event.pos().x()
            )

            self.dragging = False

            self.sliderReleased.emit()

            event.accept()
            return

        super().mouseReleaseEvent(event)


# ============================================================
# КНОПКА
# ============================================================

class AnimatedButton(QPushButton):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setCursor(
            Qt.PointingHandCursor
        )


# ============================================================
# ФОН
# ============================================================

class BackgroundWidget(QWidget):

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.settings = settings

        self.pixmap = QPixmap()
        self.movie = None

        self.particles = []

        self.rebuild_particles()

        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.tick
        )
        self.timer.start(33)

        self.setAttribute(
            Qt.WA_StyledBackground,
            True
        )

        self.setAutoFillBackground(False)

        self.load_background()

    def apply_settings(self, settings):
        self.settings = settings

        self.load_background()
        self.rebuild_particles()

        self.update()

    def stop_movie(self):
        if self.movie:
            try:
                self.movie.stop()
            except Exception:
                pass

        self.movie = None

    def load_background(self):
        self.stop_movie()

        self.pixmap = QPixmap()

        path = self.settings.get(
            "bg_image",
            ""
        )

        mode = self.settings.get(
            "bg_mode",
            "color"
        )

        if (
            mode == "image"
            and
            path
            and
            os.path.exists(path)
        ):
            if is_gif(path):
                self.movie = QMovie(path)

                if self.movie.isValid():
                    self.movie.frameChanged.connect(
                        self.on_gif_frame
                    )
                    self.movie.start()
            else:
                self.pixmap = QPixmap(path)

        self.update()

    def on_gif_frame(self, frame):
        if self.movie:
            self.pixmap = self.movie.currentPixmap()
            self.update()

    def resizeEvent(self, event):
        self.update()
        super().resizeEvent(event)

    def rebuild_particles(self):
        try:
            count = int(
                self.settings.get(
                    "particle_count",
                    80
                )
            )
        except Exception:
            count = 80

        count = max(
            0,
            min(
                500,
                count
            )
        )

        self.particles = [
            self.new_particle()
            for _ in range(count)
        ]

    def new_particle(self, x=None, y=None):
        try:
            max_size = float(
                self.settings.get(
                    "particle_size",
                    3
                )
            )
        except Exception:
            max_size = 3

        return {
            "x": (
                random.random()
                if x is None
                else x
            ),
            "y": (
                random.random()
                if y is None
                else y
            ),
            "size": random.uniform(
                1,
                max(
                    1,
                    max_size
                )
            ),
            "speed": random.uniform(
                0.5,
                1.5
            ),
            "phase": random.random() * math.tau,
            "drift": random.uniform(
                -0.35,
                0.35
            ),
        }

    def tick(self):
        try:
            mode = self.settings.get(
                "particles",
                "none"
            )

            if mode == "none":
                return

            speed = (
                float(
                    self.settings.get(
                        "particle_speed",
                        45
                    )
                )
                / 1000
            )

            current_time = time.time()

            for p in self.particles:

                if mode == "rain":
                    p["y"] += (
                        speed
                        * p["speed"]
                        * 1.9
                    )

                    p["x"] += (
                        p["drift"]
                        * speed
                        * 0.15
                    )

                elif mode == "snow":
                    p["y"] += (
                        speed
                        * p["speed"]
                        * 0.55
                    )

                    p["x"] += (
                        math.sin(
                            current_time * 1.4
                            + p["phase"]
                        )
                        * speed
                        * 0.6
                    )

                elif mode == "bubbles":
                    p["y"] -= (
                        speed
                        * p["speed"]
                        * 0.5
                    )

                    p["x"] += (
                        math.sin(
                            current_time
                            + p["phase"]
                        )
                        * speed
                        * 0.25
                    )

                else:
                    p["x"] += (
                        p["drift"]
                        * speed
                        * 0.15
                    )

                    p["y"] += (
                        math.sin(
                            current_time * 0.7
                            + p["phase"]
                        )
                        * speed
                        * 0.02
                    )

                if (
                    p["y"] < -0.05
                    or
                    p["y"] > 1.05
                    or
                    p["x"] < -0.05
                    or
                    p["x"] > 1.05
                ):
                    new = self.new_particle()

                    if mode in ("rain", "snow"):
                        new["x"] = random.random()
                        new["y"] = -0.02

                    elif mode == "bubbles":
                        new["x"] = random.random()
                        new["y"] = 1.02

                    p.update(new)

            self.update()

        except Exception:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.SmoothPixmapTransform
        )

        rect = self.rect()

        if not self.pixmap.isNull():
            scaled = self.pixmap.scaled(
                rect.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )

            x = max(
                0,
                (
                    scaled.width()
                    -
                    rect.width()
                ) // 2
            )

            y = max(
                0,
                (
                    scaled.height()
                    -
                    rect.height()
                ) // 2
            )

            source = QRect(
                int(x),
                int(y),
                rect.width(),
                rect.height()
            )

            opacity = (
                max(
                    0,
                    min(
                        100,
                        int(
                            self.settings.get(
                                "bg_opacity",
                                100
                            )
                        )
                    )
                )
                / 100
            )

            painter.save()
            painter.setOpacity(opacity)

            painter.drawPixmap(
                rect,
                scaled,
                source
            )

            painter.restore()

            darkness = max(
                0,
                min(
                    100,
                    int(
                        self.settings.get(
                            "bg_darkness",
                            25
                        )
                    )
                )
            )

            if darkness:
                painter.fillRect(
                    rect,
                    QColor(
                        0,
                        0,
                        0,
                        round(
                            255
                            * darkness
                            / 100
                        )
                    )
                )

        else:
            painter.fillRect(
                rect,
                QColor(
                    self.settings.get(
                        "bg_color",
                        "#0b0d10"
                    )
                )
            )

        mode = self.settings.get(
            "particles",
            "none"
        )

        if mode == "none":
            return

        color = (
            self.settings.get(
                "particle_color"
            )
            or
            self.settings.get(
                "accent",
                "#1db954"
            )
        )

        alpha = round(
            255
            *
            max(
                0,
                min(
                    100,
                    int(
                        self.settings.get(
                            "particle_opacity",
                            80
                        )
                    )
                )
            )
            /
            100
        )

        pen_color = QColor(color)
        pen_color.setAlpha(alpha)

        painter.setPen(
            QPen(
                pen_color,
                1
            )
        )

        painter.setBrush(
            QBrush(
                pen_color
            )
        )

        for p in self.particles:
            x = int(
                p["x"]
                * rect.width()
            )

            y = int(
                p["y"]
                * rect.height()
            )

            size = max(
                1,
                int(p["size"])
            )

            if mode == "rain":
                painter.drawLine(
                    x,
                    y,
                    x - 2,
                    y + size * 4
                )

            elif mode in ("snow", "stars"):
                painter.drawEllipse(
                    x,
                    y,
                    size,
                    size
                )

            elif mode == "sparks":
                painter.drawLine(
                    x - size,
                    y,
                    x + size,
                    y
                )

                painter.drawLine(
                    x,
                    y - size,
                    x,
                    y + size
                )

            elif mode == "bubbles":
                painter.setBrush(
                    Qt.NoBrush
                )

                painter.drawEllipse(
                    x,
                    y,
                    size * 2,
                    size * 2
                )

                painter.setBrush(
                    QBrush(
                        pen_color
                    )
                )


# ============================================================
# ОБЛОЖКА
# ============================================================

class CoverLabel(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.radius = 18
        self.movie = None

        self.setAlignment(
            Qt.AlignCenter
        )

        self.setStyleSheet(
            "background:transparent;border:none;"
        )

        self.setMinimumSize(
            120,
            120
        )

    def stop_movie(self):
        if self.movie:
            try:
                self.movie.stop()
            except Exception:
                pass

        self.movie = None

    def set_animated_cover(self, path):
        self.stop_movie()

        if not path or not os.path.exists(path):
            self.setPixmap(QPixmap())
            self.setText("Нет обложки")
            self.update()
            return

        if is_gif(path):
            movie = QMovie(path)

            if movie.isValid():
                movie.setCacheMode(
                    QMovie.CacheAll
                )

                self.movie = movie

                self.movie.frameChanged.connect(
                    self.on_movie_frame
                )

                self.movie.start()

                self.setText("")
                self.update()

                return

        pixmap = QPixmap(path)

        if pixmap.isNull():
            self.setPixmap(QPixmap())
            self.setText("Не удалось загрузить")
            return

        self.setText("")
        self.setPixmap(pixmap)
        self.update()

    def on_movie_frame(self):
        if self.movie:
            self.setPixmap(
                self.movie.currentPixmap()
            )
            self.update()

    def set_radius(self, radius):
        self.radius = max(
            0,
            int(radius)
        )

        self.update_mask()
        self.update()

    def update_mask(self):
        if self.width() <= 0 or self.height() <= 0:
            return

        r = min(
            self.radius,
            min(
                self.width(),
                self.height()
            ) // 2
        )

        if r <= 0:
            self.clearMask()
            return

        region = QRegion(
            self.rect(),
            QRegion.Rectangle
        )

        center = QRegion(
            r,
            0,
            max(
                1,
                self.width() - r * 2
            ),
            self.height(),
            QRegion.Rectangle
        )

        middle = QRegion(
            0,
            r,
            self.width(),
            max(
                1,
                self.height() - r * 2
            ),
            QRegion.Rectangle
        )

        region = center.united(middle)

        corners = [
            (0, 0),
            (
                self.width() - r * 2,
                0
            ),
            (
                0,
                self.height() - r * 2
            ),
            (
                self.width() - r * 2,
                self.height() - r * 2
            )
        ]

        for x, y in corners:
            region = region.united(
                QRegion(
                    x,
                    y,
                    r * 2,
                    r * 2,
                    QRegion.Ellipse
                )
            )

        self.setMask(region)

    def resizeEvent(self, event):
        self.update_mask()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.setRenderHint(
            QPainter.SmoothPixmapTransform
        )

        rect = self.rect()

        radius = min(
            self.radius,
            min(
                self.width(),
                self.height()
            ) // 2
        )

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor(
                25,
                28,
                34,
                150
            )
        )

        painter.drawRoundedRect(
            rect,
            radius,
            radius
        )

        pm = self.pixmap()

        if pm and not pm.isNull():
            scaled = pm.scaled(
                rect.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )

            sx = max(
                0,
                (
                    scaled.width()
                    -
                    rect.width()
                ) // 2
            )

            sy = max(
                0,
                (
                    scaled.height()
                    -
                    rect.height()
                ) // 2
            )

            painter.drawPixmap(
                rect,
                scaled,
                QRect(
                    sx,
                    sy,
                    rect.width(),
                    rect.height()
                )
            )

        elif self.text():
            painter.setPen(
                QColor(
                    220,
                    220,
                    220
                )
            )

            painter.drawText(
                rect,
                Qt.AlignCenter,
                self.text()
            )


# ============================================================
# ЭКВАЛАЙЗЕР
# ============================================================

class VisualizerWidget(QWidget):

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.active = False

        self.levels = []
        self.peaks = []

        self.reset_levels()

        self.setMinimumHeight(150)
        self.setMinimumWidth(180)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.tick
        )

        self.timer.start(50)

    def reset_levels(self):
        count = max(
            6,
            min(
                40,
                int(
                    self.settings.get(
                        "eq_bars",
                        18
                    )
                )
            )
        )

        self.levels = [0.0] * count
        self.peaks = [0.0] * count

    def apply_settings(self, settings):
        self.settings = settings
        self.reset_levels()
        self.update()

    def set_active(self, active):
        self.active = active

    def tick(self):
        try:
            speed = max(
                0.05,
                float(
                    self.settings.get(
                        "eq_speed",
                        55
                    )
                ) / 100
            )

            for i in range(
                len(self.levels)
            ):
                target = (
                    random.random()
                    if self.active
                    else 0
                )

                self.levels[i] += (
                    target
                    -
                    self.levels[i]
                ) * speed

                self.peaks[i] = max(
                    self.levels[i],
                    self.peaks[i] - 0.035
                )

            self.update()

        except Exception:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        count = len(self.levels)

        if count <= 0:
            return

        gap = 4

        bar_width = max(
            2,
            (
                self.width()
                -
                gap * (count + 1)
            )
            / count
        )

        color = QColor(
            self.settings.get(
                "eq_color"
            )
            or
            self.settings.get(
                "accent",
                "#1db954"
            )
        )

        mirror = (
            self.settings.get(
                "eq_style"
            )
            ==
            "mirror"
        )

        for i in range(count):
            x = int(
                gap
                +
                i * (
                    bar_width
                    + gap
                )
            )

            height = max(
                2,
                int(
                    self.levels[i]
                    * (
                        self.height()
                        - 10
                    )
                )
            )

            painter.setPen(Qt.NoPen)
            painter.setBrush(color)

            if mirror:
                mid = self.height() // 2

                painter.drawRoundedRect(
                    x,
                    mid - height // 2,
                    int(bar_width),
                    height,
                    3,
                    3
                )

            else:
                painter.drawRoundedRect(
                    x,
                    self.height() - height,
                    int(bar_width),
                    height,
                    3,
                    3
                )


# ============================================================
# СТИЛИ
# ============================================================

def style_for(settings):

    dark = (
        settings.get(
            "theme",
            "dark"
        )
        ==
        "dark"
    )

    accent = settings.get(
        "accent",
        "#1db954"
    )

    if dark:
        bg = "#111318"
        card = "#171a20"
        card2 = "#1d2129"
        text = "#f5f7fa"
        sub = "#a6adb8"
        border = "#303641"

    else:
        bg = "#f3f5f7"
        card = "#ffffff"
        card2 = "#eef1f4"
        text = "#111318"
        sub = "#5f6772"
        border = "#d7dce2"

    panel_opacity = settings.get(
        "panel_opacity",
        90
    )

    playlist_opacity = settings.get(
        "playlist_opacity",
        75
    )

    track_opacity = settings.get(
        "track_opacity",
        75
    )

    card_alpha = rgba(
        card,
        panel_opacity
    )

    playlist_alpha = rgba(
        card2,
        playlist_opacity
    )

    track_alpha = rgba(
        card,
        track_opacity
    )

    font_family = settings.get(
        "font_family",
        "Segoe UI"
    )

    font_size = settings.get(
        "font_size",
        13
    )

    return f"""
QWidget {{
    color: {text};
    font-family: "{font_family}";
    font-size: {font_size}px;
}}

QMainWindow, QDialog {{
    background: {bg};
}}

QFrame#card {{
    background: {card_alpha};
    border: 1px solid {border};
    border-radius: 14px;
}}

QLabel#title {{
    font-size: 18px;
    font-weight: 700;
}}

QLabel#section {{
    color: {sub};
    font-size: 11px;
    font-weight: 700;
}}

QLabel#muted {{
    color: {sub};
}}

QLabel#songTitle {{
    color: {text};
    font-size: 17px;
    font-weight: 700;
}}

QLabel#songArtist {{
    color: {sub};
    font-size: 13px;
}}

QPushButton {{
    background: {playlist_alpha};
    color: {text};
    border: 1px solid {border};
    border-radius: 9px;
    padding: 8px 12px;
}}

QPushButton:hover {{
    border-color: {accent};
    color: {accent};
}}

QPushButton:pressed {{
    background: {accent};
    color: white;
}}

QPushButton#primary {{
    background: {accent};
    color: white;
    border: none;
    font-weight: 700;
}}

QPushButton#shuffle {{
    background: {accent};
    color: white;
    border: none;
    font-weight: 700;
}}

QPushButton#danger {{
    background: rgba(180,45,55,170);
    color: white;
    border: none;
}}

QPushButton#danger:hover {{
    background: rgba(220,55,65,220);
}}

QListWidget {{
    background: {track_alpha};
    color: {text};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 5px;
}}

QListWidget#playlistList {{
    background: {playlist_alpha};
}}

QListWidget#trackList {{
    background: {track_alpha};
}}

QListWidget::item {{
    padding: 10px;
    border-radius: 8px;
}}

QListWidget::item:hover {{
    background: rgba(255,255,255,20);
}}

QListWidget::item:selected {{
    background: {accent};
    color: white;
}}

QLineEdit,
QComboBox {{
    background: {playlist_alpha};
    color: {text};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 7px;
}}

QComboBox QAbstractItemView {{
    background: {card2};
    color: {text};
    selection-background-color: {accent};
}}

QTabWidget::pane {{
    border: 1px solid {border};
    background: {card_alpha};
    border-radius: 10px;
}}

QTabBar::tab {{
    background: {playlist_alpha};
    color: {sub};
    padding: 8px 14px;
    margin: 3px;
    border-radius: 8px;
}}

QTabBar::tab:selected {{
    background: {accent};
    color: white;
}}

QSlider::groove:horizontal {{
    height: 5px;
    background: {border};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: {accent};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {accent};
    width: 13px;
    margin: -4px 0;
    border-radius: 6px;
}}

QGroupBox {{
    border: 1px solid {border};
    border-radius: 10px;
    margin-top: 10px;
    padding: 10px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}}
"""


# ============================================================
# НАСТРОЙКИ
# ============================================================

class SettingsDialog(QDialog):

    def __init__(self, settings, themes, parent=None):
        super().__init__(parent)

        self.settings = dict(settings)
        self.themes = dict(themes)

        self.setWindowTitle(
            "Настройки — MPlayer by Nikson"
        )

        self.setMinimumSize(
            780,
            680
        )

        self.setStyleSheet(
            style_for(self.settings)
        )

        tabs = QTabWidget()

        tabs.addTab(
            self.appearance_tab(),
            "Оформление"
        )

        tabs.addTab(
            self.background_tab(),
            "Фон и частицы"
        )

        tabs.addTab(
            self.cover_tab(),
            "Обложка"
        )

        tabs.addTab(
            self.eq_tab(),
            "Эквалайзер"
        )

        tabs.addTab(
            self.audio_tab(),
            "Звук"
        )

        tabs.addTab(
            self.themes_tab(),
            "Темы"
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            |
            QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            self.accept
        )

        buttons.rejected.connect(
            self.reject
        )

        layout = QVBoxLayout(self)

        layout.addWidget(tabs)
        layout.addWidget(buttons)

    def make_slider(self, value, minimum, maximum):
        slider = ClickableSlider(
            Qt.Horizontal
        )

        slider.setRange(
            minimum,
            maximum
        )

        slider.setValue(
            int(value)
        )

        return slider

    # --------------------------------------------------------
    # ОФОРМЛЕНИЕ
    # --------------------------------------------------------

    def appearance_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)

        self.theme = QComboBox()

        self.theme.addItems([
            "Тёмная",
            "Светлая"
        ])

        self.theme.setCurrentIndex(
            0
            if
            self.settings.get(
                "theme"
            ) == "dark"
            else 1
        )

        self.accent = QPushButton(
            self.settings.get(
                "accent",
                "#1db954"
            )
        )

        self.accent.clicked.connect(
            self.pick_accent
        )

        self.font = QComboBox()

        fonts = [
            "Segoe UI",
            "Arial",
            "Calibri",
            "Tahoma",
            "Verdana",
            "Trebuchet MS",
            "Times New Roman",
            "Consolas",
            "Courier New",
            "Georgia",
            "Comic Sans MS"
        ]

        self.font.addItems(fonts)

        current_font = self.settings.get(
            "font_family",
            "Segoe UI"
        )

        if current_font in fonts:
            self.font.setCurrentText(
                current_font
            )

        self.font_size = self.make_slider(
            self.settings.get(
                "font_size",
                13
            ),
            9,
            22
        )

        self.opacity = self.make_slider(
            self.settings.get(
                "panel_opacity",
                90
            ),
            20,
            100
        )

        self.playlist_opacity = self.make_slider(
            self.settings.get(
                "playlist_opacity",
                75
            ),
            10,
            100
        )

        self.track_opacity = self.make_slider(
            self.settings.get(
                "track_opacity",
                75
            ),
            10,
            100
        )

        form.addRow(
            "Тема:",
            self.theme
        )

        form.addRow(
            "Акцентный цвет:",
            self.accent
        )

        form.addRow(
            "Шрифт:",
            self.font
        )

        form.addRow(
            "Размер шрифта:",
            self.font_size
        )

        form.addRow(
            "Прозрачность панелей:",
            self.opacity
        )

        form.addRow(
            "Прозрачность плейлистов:",
            self.playlist_opacity
        )

        form.addRow(
            "Прозрачность песен:",
            self.track_opacity
        )

        return widget

    def pick_accent(self):
        color = QColorDialog.getColor(
            QColor(
                self.settings.get(
                    "accent",
                    "#1db954"
                )
            ),
            self
        )

        if color.isValid():
            self.settings["accent"] = color.name()
            self.accent.setText(
                color.name()
            )

    # --------------------------------------------------------
    # ФОН
    # --------------------------------------------------------

    def background_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)

        self.bg_mode = QComboBox()

        self.bg_mode.addItems([
            "Однотонный цвет",
            "Фотография / GIF"
        ])

        self.bg_mode.setCurrentIndex(
            1
            if
            self.settings.get(
                "bg_mode"
            ) == "image"
            else 0
        )

        self.bg_color = QPushButton(
            self.settings.get(
                "bg_color",
                "#0b0d10"
            )
        )

        self.bg_color.clicked.connect(
            self.pick_bg_color
        )

        self.bg_path = QLineEdit(
            self.settings.get(
                "bg_image",
                ""
            )
        )

        choose = QPushButton(
            "Выбрать фото / GIF"
        )

        choose.clicked.connect(
            self.pick_bg
        )

        row = QHBoxLayout()

        row.addWidget(
            self.bg_path
        )

        row.addWidget(
            choose
        )

        wrapper = QWidget()
        wrapper.setLayout(row)

        self.darkness = self.make_slider(
            self.settings.get(
                "bg_darkness",
                25
            ),
            0,
            90
        )

        self.bg_opacity = self.make_slider(
            self.settings.get(
                "bg_opacity",
                100
            ),
            0,
            100
        )

        self.particles = QComboBox()

        self.particles.addItems([
            "Нет",
            "Дождь",
            "Снег",
            "Звёзды",
            "Искры",
            "Пузырьки"
        ])

        particle_map = {
            "none": 0,
            "rain": 1,
            "snow": 2,
            "stars": 3,
            "sparks": 4,
            "bubbles": 5
        }

        self.particles.setCurrentIndex(
            particle_map.get(
                self.settings.get(
                    "particles",
                    "none"
                ),
                0
            )
        )

        self.p_count = self.make_slider(
            self.settings.get(
                "particle_count",
                80
            ),
            0,
            500
        )

        self.p_speed = self.make_slider(
            self.settings.get(
                "particle_speed",
                45
            ),
            5,
            150
        )

        self.p_size = self.make_slider(
            self.settings.get(
                "particle_size",
                3
            ),
            1,
            10
        )

        self.p_opacity = self.make_slider(
            self.settings.get(
                "particle_opacity",
                80
            ),
            5,
            100
        )

        self.p_color = QPushButton(
            self.settings.get(
                "particle_color"
            )
            or
            "Как акцент"
        )

        self.p_color.clicked.connect(
            self.pick_particle_color
        )

        form.addRow(
            "Тип фона:",
            self.bg_mode
        )

        form.addRow(
            "Цвет:",
            self.bg_color
        )

        form.addRow(
            "Фотография / GIF:",
            wrapper
        )

        form.addRow(
            "Затемнение:",
            self.darkness
        )

        form.addRow(
            "Прозрачность:",
            self.bg_opacity
        )

        form.addRow(
            "Эффект частиц:",
            self.particles
        )

        form.addRow(
            "Количество:",
            self.p_count
        )

        form.addRow(
            "Скорость:",
            self.p_speed
        )

        form.addRow(
            "Размер:",
            self.p_size
        )

        form.addRow(
            "Прозрачность частиц:",
            self.p_opacity
        )

        form.addRow(
            "Цвет частиц:",
            self.p_color
        )

        info = QLabel(
            "GIF-фон будет проигрываться автоматически."
        )

        info.setWordWrap(True)

        form.addRow(
            "",
            info
        )

        return widget

    def pick_bg_color(self):
        color = QColorDialog.getColor(
            QColor(
                self.settings.get(
                    "bg_color",
                    "#0b0d10"
                )
            ),
            self
        )

        if color.isValid():
            self.settings["bg_color"] = color.name()
            self.bg_color.setText(
                color.name()
            )

    def pick_bg(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите фон",
            "",
            "Изображения/GIF (*.png *.jpg *.jpeg *.bmp *.webp *.gif)"
        )

        if path:
            copied = copy_asset(
                path,
                ASSETS_DIR,
                "background"
            )

            self.bg_path.setText(
                copied or path
            )

            self.bg_mode.setCurrentIndex(1)

    def pick_particle_color(self):
        color = QColorDialog.getColor(
            QColor(
                self.settings.get(
                    "particle_color"
                )
                or
                self.settings.get(
                    "accent",
                    "#1db954"
                )
            ),
            self
        )

        if color.isValid():
            self.settings["particle_color"] = color.name()
            self.p_color.setText(
                color.name()
            )

    # --------------------------------------------------------
    # ОБЛОЖКА
    # --------------------------------------------------------

    def cover_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)

        self.cover_path = QLineEdit(
            self.settings.get(
                "cover_path",
                ""
            )
        )

        choose = QPushButton(
            "Выбрать обложку / GIF"
        )

        choose.clicked.connect(
            self.pick_cover
        )

        row = QHBoxLayout()

        row.addWidget(
            self.cover_path
        )

        row.addWidget(
            choose
        )

        wrapper = QWidget()
        wrapper.setLayout(row)

        self.cover_size = self.make_slider(
            self.settings.get(
                "cover_size",
                220
            ),
            120,
            500
        )

        self.cover_radius = self.make_slider(
            self.settings.get(
                "cover_radius",
                18
            ),
            0,
            60
        )

        self.cover_shadow = QComboBox()

        self.cover_shadow.addItems([
            "Нет",
            "Мягкая",
            "Сильная"
        ])

        shadow_map = {
            "none": 0,
            "soft": 1,
            "strong": 2
        }

        self.cover_shadow.setCurrentIndex(
            shadow_map.get(
                self.settings.get(
                    "cover_shadow",
                    "strong"
                ),
                2
            )
        )

        form.addRow(
            "Своя обложка / GIF:",
            wrapper
        )

        form.addRow(
            "Размер:",
            self.cover_size
        )

        form.addRow(
            "Скругление:",
            self.cover_radius
        )

        form.addRow(
            "Тень:",
            self.cover_shadow
        )

        info = QLabel(
            "GIF-обложка будет анимироваться прямо в плеере."
        )

        info.setWordWrap(True)

        form.addRow(
            "",
            info
        )

        return widget

    def pick_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите обложку",
            "",
            "Изображения/GIF (*.png *.jpg *.jpeg *.bmp *.webp *.gif)"
        )

        if path:
            copied = copy_asset(
                path,
                COVERS_DIR,
                "custom_cover"
            )

            self.cover_path.setText(
                copied or path
            )

    # --------------------------------------------------------
    # ЭКВАЛАЙЗЕР
    # --------------------------------------------------------

    def eq_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)

        self.eq_preset = QComboBox()

        self.eq_preset.addItems(
            list(EQ_PRESETS.keys())
        )

        self.eq_preset.setCurrentText(
            self.settings.get(
                "eq_preset",
                "Flat"
            )
        )

        self.eq_bars = self.make_slider(
            self.settings.get(
                "eq_bars",
                18
            ),
            6,
            40
        )

        self.eq_speed = self.make_slider(
            self.settings.get(
                "eq_speed",
                55
            ),
            10,
            100
        )

        self.eq_style = QComboBox()

        self.eq_style.addItems([
            "Столбцы",
            "Зеркальный"
        ])

        self.eq_style.setCurrentIndex(
            1
            if
            self.settings.get(
                "eq_style"
            ) == "mirror"
            else 0
        )

        self.eq_color = QPushButton(
            self.settings.get(
                "eq_color"
            )
            or
            "Как акцент"
        )

        self.eq_color.clicked.connect(
            self.pick_eq_color
        )

        form.addRow(
            "Пресет:",
            self.eq_preset
        )

        form.addRow(
            "Количество полос:",
            self.eq_bars
        )

        form.addRow(
            "Скорость:",
            self.eq_speed
        )

        form.addRow(
            "Вид:",
            self.eq_style
        )

        form.addRow(
            "Цвет:",
            self.eq_color
        )

        return widget

    def pick_eq_color(self):
        color = QColorDialog.getColor(
            QColor(
                self.settings.get(
                    "eq_color"
                )
                or
                self.settings.get(
                    "accent",
                    "#1db954"
                )
            ),
            self
        )

        if color.isValid():
            self.settings["eq_color"] = color.name()
            self.eq_color.setText(
                color.name()
            )

    # --------------------------------------------------------
    # ЗВУК
    # --------------------------------------------------------

    def audio_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)

        self.volume = self.make_slider(
            self.settings.get(
                "volume",
                70
            ),
            0,
            100
        )

        self.bass = self.make_slider(
            self.settings.get(
                "bass",
                0
            ),
            -12,
            12
        )

        self.treble = self.make_slider(
            self.settings.get(
                "treble",
                0
            ),
            -12,
            12
        )

        self.balance = self.make_slider(
            self.settings.get(
                "balance",
                0
            ),
            -100,
            100
        )

        self.preamp = self.make_slider(
            self.settings.get(
                "preamp",
                0
            ),
            -12,
            12
        )

        form.addRow(
            "Громкость:",
            self.volume
        )

        form.addRow(
            "Бас:",
            self.bass
        )

        form.addRow(
            "Высокие:",
            self.treble
        )

        form.addRow(
            "Баланс:",
            self.balance
        )

        form.addRow(
            "Предусилитель:",
            self.preamp
        )

        return widget

    # --------------------------------------------------------
    # ТЕМЫ
    # --------------------------------------------------------

    def themes_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = QLabel(
            "Сохраняйте полный набор настроек оформления "
            "и применяйте их позже."
        )

        info.setWordWrap(True)

        layout.addWidget(info)

        self.theme_list = QListWidget()

        for name in self.themes:
            self.theme_list.addItem(name)

        layout.addWidget(
            self.theme_list
        )

        buttons = QHBoxLayout()

        save_button = QPushButton(
            "💾 Сохранить текущую тему"
        )

        save_button.clicked.connect(
            self.save_current_theme
        )

        buttons.addWidget(
            save_button
        )

        load_button = QPushButton(
            "▶ Применить выбранную"
        )

        load_button.clicked.connect(
            self.load_selected_theme
        )

        buttons.addWidget(
            load_button
        )

        delete_button = QPushButton(
            "🗑 Удалить"
        )

        delete_button.clicked.connect(
            self.delete_selected_theme
        )

        buttons.addWidget(
            delete_button
        )

        layout.addLayout(buttons)

        return widget

    def save_current_theme(self):
        name, ok = QInputDialog.getText(
            self,
            "Сохранение темы",
            "Название темы:"
        )

        if not ok:
            return

        name = name.strip()

        if not name:
            return

        data = self.result()

        self.themes[name] = dict(data)

        save_themes(self.themes)

        existing = self.theme_list.findItems(
            name,
            Qt.MatchExactly
        )

        if not existing:
            self.theme_list.addItem(name)

        QMessageBox.information(
            self,
            APP_NAME,
            f"Тема «{name}» сохранена."
        )

    def load_selected_theme(self):
        item = self.theme_list.currentItem()

        if not item:
            QMessageBox.information(
                self,
                APP_NAME,
                "Выберите сохранённую тему."
            )
            return

        name = item.text()

        theme = self.themes.get(name)

        if not isinstance(theme, dict):
            return

        self.settings.update(theme)

        QMessageBox.information(
            self,
            APP_NAME,
            f"Тема «{name}» загружена.\n\n"
            "Нажмите «Save», чтобы применить её."
        )

    def delete_selected_theme(self):
        item = self.theme_list.currentItem()

        if not item:
            return

        name = item.text()

        answer = QMessageBox.question(
            self,
            "Удаление темы",
            f"Удалить тему «{name}»?",
            QMessageBox.Yes |
            QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        self.themes.pop(
            name,
            None
        )

        save_themes(
            self.themes
        )

        self.theme_list.takeItem(
            self.theme_list.row(item)
        )

    # --------------------------------------------------------
    # РЕЗУЛЬТАТ
    # --------------------------------------------------------

    def result(self):
        settings = dict(self.settings)

        settings["theme"] = (
            "dark"
            if self.theme.currentIndex() == 0
            else "light"
        )

        settings["font_family"] = (
            self.font.currentText()
        )

        settings["font_size"] = (
            self.font_size.value()
        )

        settings["panel_opacity"] = (
            self.opacity.value()
        )

        settings["playlist_opacity"] = (
            self.playlist_opacity.value()
        )

        settings["track_opacity"] = (
            self.track_opacity.value()
        )

        settings["bg_mode"] = (
            "image"
            if self.bg_mode.currentIndex() == 1
            else "color"
        )

        settings["bg_image"] = (
            self.bg_path.text().strip()
        )

        settings["bg_color"] = (
            self.bg_color.text().strip()
        )

        settings["bg_darkness"] = (
            self.darkness.value()
        )

        settings["bg_opacity"] = (
            self.bg_opacity.value()
        )

        particle_values = [
            "none",
            "rain",
            "snow",
            "stars",
            "sparks",
            "bubbles"
        ]

        settings["particles"] = (
            particle_values[
                self.particles.currentIndex()
            ]
        )

        settings["particle_count"] = (
            self.p_count.value()
        )

        settings["particle_speed"] = (
            self.p_speed.value()
        )

        settings["particle_size"] = (
            self.p_size.value()
        )

        settings["particle_opacity"] = (
            self.p_opacity.value()
        )

        settings["particle_color"] = (
            ""
            if self.p_color.text() == "Как акцент"
            else self.p_color.text()
        )

        settings["cover_path"] = (
            self.cover_path.text().strip()
        )

        settings["cover_size"] = (
            self.cover_size.value()
        )

        settings["cover_radius"] = (
            self.cover_radius.value()
        )

        shadow_values = [
            "none",
            "soft",
            "strong"
        ]

        settings["cover_shadow"] = (
            shadow_values[
                self.cover_shadow.currentIndex()
            ]
        )

        settings["eq_preset"] = (
            self.eq_preset.currentText()
        )

        settings["eq_bars"] = (
            self.eq_bars.value()
        )

        settings["eq_speed"] = (
            self.eq_speed.value()
        )

        settings["eq_style"] = (
            "mirror"
            if self.eq_style.currentIndex()
            else "bars"
        )

        settings["eq_color"] = (
            ""
            if self.eq_color.text() == "Как акцент"
            else self.eq_color.text()
        )

        settings["volume"] = self.volume.value()
        settings["bass"] = self.bass.value()
        settings["treble"] = self.treble.value()
        settings["balance"] = self.balance.value()
        settings["preamp"] = self.preamp.value()

        return settings


# ============================================================
# WORKER ССЫЛКИ
# ============================================================

class TrackWorker(QThread):

    finished_ok = pyqtSignal(dict)
    finished_err = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        if not HAS_YTDLP:
            self.finished_err.emit(
                "Установите yt-dlp:\n\n"
                "python -m pip install yt-dlp"
            )
            return

        try:
            self.progress.emit(
                "Получаю метаданные..."
            )

            options = {
                "quiet": True,
                "skip_download": True,
                "noplaylist": True,
                "format": "bestaudio/best"
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(
                    self.url,
                    download=False
                )

            track = {
                "title": (
                    info.get("title")
                    or
                    "Без названия"
                ),

                "artist": (
                    info.get("artist")
                    or
                    info.get("uploader")
                    or
                    ""
                ),

                "type": "remote",

                "webpage_url": self.url,

                "stream_url": info.get("url"),

                "duration": float(
                    info.get("duration")
                    or
                    0
                ),

                "cover": None,

                "cover_url": (
                    info.get("thumbnail")
                )
            }

            self.finished_ok.emit(track)

        except Exception as e:
            self.finished_err.emit(str(e))


# ============================================================
# WORKER РАЗРЕШЕНИЯ ССЫЛКИ
# ============================================================

class ResolveWorker(QThread):

    finished_ok = pyqtSignal(dict, object)
    finished_err = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, track):
        super().__init__()

        self.track = dict(track)

    def run(self):
        if not HAS_YTDLP:
            self.finished_err.emit(
                "Установите yt-dlp."
            )
            return

        try:
            self.progress.emit(
                "Ищу аудио..."
            )

            options = {
                "quiet": True,
                "skip_download": True,
                "noplaylist": True,
                "format": "bestaudio/best"
            }

            with yt_dlp.YoutubeDL(options) as ydl:

                url = self.track.get(
                    "webpage_url"
                )

                if not url:
                    query = (
                        self.track.get(
                            "search_query"
                        )
                        or
                        self.track.get(
                            "title"
                        )
                    )

                    info = ydl.extract_info(
                        "ytsearch1:" + query,
                        download=False
                    )

                    entries = (
                        info.get("entries")
                        or
                        []
                    )

                    if not entries:
                        raise RuntimeError(
                            "Трек не найден."
                        )

                    chosen = entries[0]

                    url = chosen.get(
                        "webpage_url"
                    )

                    self.track[
                        "webpage_url"
                    ] = url

                    self.track[
                        "cover_url"
                    ] = (
                        self.track.get(
                            "cover_url"
                        )
                        or
                        chosen.get(
                            "thumbnail"
                        )
                    )

                    self.track[
                        "duration"
                    ] = float(
                        self.track.get(
                            "duration"
                        )
                        or
                        chosen.get(
                            "duration"
                        )
                        or
                        0
                    )

                info = ydl.extract_info(
                    url,
                    download=False
                )

                stream = info.get("url")

                self.track[
                    "duration"
                ] = float(
                    self.track.get(
                        "duration"
                    )
                    or
                    info.get(
                        "duration"
                    )
                    or
                    0
                )

                self.track[
                    "cover_url"
                ] = (
                    self.track.get(
                        "cover_url"
                    )
                    or
                    info.get(
                        "thumbnail"
                    )
                )

            if not stream:
                raise RuntimeError(
                    "Аудиопоток не найден."
                )

            self.track[
                "stream_url"
            ] = stream

            self.progress.emit(
                "Загружаю аудио..."
            )

            data = (
                urllib.request
                .urlopen(
                    stream,
                    timeout=30
                )
                .read()
            )

            self.finished_ok.emit(
                self.track,
                io.BytesIO(data)
            )

        except Exception as e:
            self.finished_err.emit(str(e))


# ============================================================
# ГЛАВНОЕ ОКНО
# ============================================================

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        try:
            pygame.mixer.init()
        except Exception as e:
            QMessageBox.critical(
                self,
                APP_NAME,
                "Не удалось запустить pygame:\n\n"
                f"{e}"
            )

        self.settings = load_settings()
        self.themes = load_themes()

        data = load_playlists()

        self.playlists = data["playlists"]
        self.library = data["library"]

        self.current_playlist = next(
            iter(self.playlists)
        )

        self.current_index = -1
        self.current_track = None

        self.active_list = []
        self.play_order = []

        self.is_playing = False
        self.is_paused = False

        self.track_length = 0

        self.play_start_offset = 0
        self.play_started_at = 0

        self.user_seeking = False

        self.worker = None

        self.setWindowTitle(
            APP_NAME
        )

        self.resize(
            1200,
            780
        )

        if os.path.exists(ICON_PATH):
            self.setWindowIcon(
                QIcon(ICON_PATH)
            )

        self.build_ui()
        self.apply_appearance()
        self.refresh_all()

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.update_progress
        )

        self.timer.start(300)

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        self.bg = BackgroundWidget(
            self.settings
        )

        self.setCentralWidget(
            self.bg
        )

        root = QVBoxLayout(self.bg)

        root.setContentsMargins(
            18,
            14,
            18,
            18
        )

        root.setSpacing(10)

        # ----------------------------------------------------
        # ВЕРХ
        # ----------------------------------------------------

        top = QHBoxLayout()

        title = QLabel(
            "MPlayer by Nikson"
        )

        title.setObjectName("title")

        top.addWidget(title)
        top.addStretch()

        self.shuffle_button = AnimatedButton(
            "🔀 Перемешать"
        )

        self.shuffle_button.clicked.connect(
            self.toggle_shuffle
        )

        top.addWidget(
            self.shuffle_button
        )

        settings_button = AnimatedButton(
            "⚙ Настройки"
        )

        settings_button.clicked.connect(
            self.open_settings
        )

        top.addWidget(
            settings_button
        )

        root.addLayout(top)

        # ----------------------------------------------------
        # SPLITTER
        # ----------------------------------------------------

        splitter = QSplitter(
            Qt.Horizontal
        )

        root.addWidget(
            splitter,
            1
        )

        # ====================================================
        # ПЛЕЙЛИСТЫ
        # ====================================================

        left = QFrame()
        left.setObjectName("card")

        left_layout = QVBoxLayout(left)

        label = QLabel("ПЛЕЙЛИСТЫ")
        label.setObjectName("section")

        left_layout.addWidget(label)

        self.playlist_list = QListWidget()
        self.playlist_list.setObjectName(
            "playlistList"
        )

        self.playlist_list.setContextMenuPolicy(
            Qt.CustomContextMenu
        )

        self.playlist_list.customContextMenuRequested.connect(
            self.playlist_context_menu
        )

        self.playlist_list.currentTextChanged.connect(
            self.select_playlist
        )

        left_layout.addWidget(
            self.playlist_list,
            1
        )

        buttons = QHBoxLayout()

        add_playlist = AnimatedButton(
            "+ Плейлист"
        )

        add_playlist.clicked.connect(
            self.create_playlist
        )

        buttons.addWidget(
            add_playlist
        )

        delete_playlist = AnimatedButton(
            "🗑 Удалить"
        )

        delete_playlist.setObjectName(
            "danger"
        )

        delete_playlist.clicked.connect(
            self.delete_playlist
        )

        buttons.addWidget(
            delete_playlist
        )

        left_layout.addLayout(buttons)

        import_button = AnimatedButton(
            "Импорт по ссылке"
        )

        import_button.clicked.connect(
            self.import_playlist
        )

        left_layout.addWidget(
            import_button
        )

        splitter.addWidget(left)

        # ====================================================
        # ПЕСНИ
        # ====================================================

        middle = QFrame()
        middle.setObjectName("card")

        middle_layout = QVBoxLayout(middle)

        label = QLabel("ПЕСНИ")
        label.setObjectName("section")

        middle_layout.addWidget(label)

        self.track_list = QListWidget()
        self.track_list.setObjectName(
            "trackList"
        )

        self.track_list.setContextMenuPolicy(
            Qt.CustomContextMenu
        )

        self.track_list.customContextMenuRequested.connect(
            self.track_context_menu
        )

        self.track_list.setDragDropMode(
            QAbstractItemView.InternalMove
        )

        self.track_list.itemDoubleClicked.connect(
            self.track_double_clicked
        )

        middle_layout.addWidget(
            self.track_list,
            1
        )

        buttons = QHBoxLayout()

        add_file = AnimatedButton(
            "Добавить файл"
        )

        add_file.clicked.connect(
            self.add_files
        )

        buttons.addWidget(add_file)

        add_link = AnimatedButton(
            "Добавить ссылку"
        )

        add_link.clicked.connect(
            self.add_link
        )

        buttons.addWidget(add_link)

        delete_song = AnimatedButton(
            "🗑 Удалить песню"
        )

        delete_song.setObjectName(
            "danger"
        )

        delete_song.clicked.connect(
            self.delete_track
        )

        buttons.addWidget(delete_song)

        middle_layout.addLayout(buttons)

        self.status = QLabel()
        self.status.setObjectName("muted")

        middle_layout.addWidget(
            self.status
        )

        splitter.addWidget(middle)

        # ====================================================
        # ПРАВАЯ ПАНЕЛЬ
        # ====================================================

        right = QFrame()
        right.setObjectName("card")

        right_layout = QVBoxLayout(right)

        self.cover = CoverLabel()

        self.cover.setText(
            "Нет обложки"
        )

        right_layout.addWidget(
            self.cover,
            alignment=Qt.AlignCenter
        )

        self.visualizer = VisualizerWidget(
            self.settings
        )

        right_layout.addWidget(
            self.visualizer
        )

        self.visualizer_title = QLabel(
            "Ничего не играет"
        )

        self.visualizer_title.setObjectName(
            "songTitle"
        )

        self.visualizer_title.setAlignment(
            Qt.AlignCenter
        )

        self.visualizer_title.setWordWrap(True)

        right_layout.addWidget(
            self.visualizer_title
        )

        self.visualizer_artist = QLabel("")

        self.visualizer_artist.setObjectName(
            "songArtist"
        )

        self.visualizer_artist.setAlignment(
            Qt.AlignCenter
        )

        self.visualizer_artist.setWordWrap(True)

        right_layout.addWidget(
            self.visualizer_artist
        )

        right_layout.addStretch()

        splitter.addWidget(right)

        splitter.setSizes([
            260,
            520,
            350
        ])

        # ====================================================
        # ПЛЕЕР
        # ====================================================

        player = QFrame()
        player.setObjectName("card")

        player_layout = QVBoxLayout(player)

        self.track_title = QLabel(
            "Ничего не играет"
        )

        self.track_title.setObjectName(
            "title"
        )

        player_layout.addWidget(
            self.track_title
        )

        seek_layout = QHBoxLayout()

        self.current_time = QLabel(
            "0:00"
        )

        seek_layout.addWidget(
            self.current_time
        )

        self.seek = ClickableSlider(
            Qt.Horizontal
        )

        self.seek.setRange(
            0,
            1000
        )

        self.seek.sliderPressed.connect(
            self.seek_started
        )

        self.seek.sliderReleased.connect(
            self.seek_released
        )

        seek_layout.addWidget(
            self.seek,
            1
        )

        self.total_time = QLabel(
            "0:00"
        )

        seek_layout.addWidget(
            self.total_time
        )

        player_layout.addLayout(
            seek_layout
        )

        controls = QHBoxLayout()

        controls.addStretch()

        previous = AnimatedButton("⏮")

        previous.clicked.connect(
            self.prev
        )

        controls.addWidget(previous)

        back = AnimatedButton("↶ 10")

        back.clicked.connect(
            lambda: self.jump(-10)
        )

        controls.addWidget(back)

        self.play_button = AnimatedButton("▶")

        self.play_button.setObjectName(
            "primary"
        )

        self.play_button.setFixedSize(
            65,
            44
        )

        self.play_button.clicked.connect(
            self.toggle
        )

        controls.addWidget(
            self.play_button
        )

        forward = AnimatedButton("↷ 10")

        forward.clicked.connect(
            lambda: self.jump(10)
        )

        controls.addWidget(forward)

        next_button = AnimatedButton("⏭")

        next_button.clicked.connect(
            self.next
        )

        controls.addWidget(next_button)

        controls.addStretch()

        controls.addWidget(
            QLabel("🔊")
        )

        self.volume = ClickableSlider(
            Qt.Horizontal
        )

        self.volume.setRange(
            0,
            100
        )

        self.volume.setFixedWidth(130)

        self.volume.setValue(
            self.settings.get(
                "volume",
                70
            )
        )

        self.volume.valueChanged.connect(
            self.volume_changed
        )

        controls.addWidget(
            self.volume
        )

        player_layout.addLayout(
            controls
        )

        root.addWidget(player)

    # ========================================================
    # ОФОРМЛЕНИЕ
    # ========================================================

    def apply_appearance(self):

        self.setStyleSheet(
            style_for(self.settings)
        )

        # ====================================================
        # НОВОЕ:
        # Цвет стандартной верхней панели Windows
        # ====================================================

        set_windows_titlebar(
            self,
            self.settings
        )

        self.bg.apply_settings(
            self.settings
        )

        self.visualizer.apply_settings(
            self.settings
        )

        size = int(
            self.settings.get(
                "cover_size",
                220
            )
        )

        self.visualizer.setMinimumHeight(
            max(
                150,
                int(size * 0.45)
            )
        )

        self.cover.setFixedSize(
            size,
            size
        )

        self.cover.set_radius(
            int(
                self.settings.get(
                    "cover_radius",
                    18
                )
            )
        )

        self.apply_cover_shadow()

        self.update_cover(
            self.current_track
        )

        self.volume.blockSignals(True)

        self.volume.setValue(
            self.settings.get(
                "volume",
                70
            )
        )

        self.volume.blockSignals(False)

        try:
            pygame.mixer.music.set_volume(
                self.settings.get(
                    "volume",
                    70
                ) / 100
            )
        except Exception:
            pass

        self.update_song_info(
            self.current_track
        )

        self.update_shuffle_button()

    def apply_cover_shadow(self):

        old = self.cover.graphicsEffect()

        if old:
            self.cover.setGraphicsEffect(None)

        mode = self.settings.get(
            "cover_shadow",
            "strong"
        )

        if mode == "none":
            return

        effect = QGraphicsDropShadowEffect(
            self.cover
        )

        if mode == "soft":
            effect.setBlurRadius(18)
            effect.setOffset(0, 5)
            effect.setColor(
                QColor(
                    0,
                    0,
                    0,
                    110
                )
            )

        else:
            effect.setBlurRadius(35)
            effect.setOffset(0, 10)
            effect.setColor(
                QColor(
                    0,
                    0,
                    0,
                    180
                )
            )

        self.cover.setGraphicsEffect(
            effect
        )

    # ========================================================
    # ОБНОВЛЕНИЕ
    # ========================================================

    def refresh_all(self):
        self.refresh_playlists()
        self.refresh_tracks()

    def refresh_playlists(self):
        self.playlist_list.blockSignals(True)

        self.playlist_list.clear()

        for name in self.playlists:
            self.playlist_list.addItem(name)

        items = self.playlist_list.findItems(
            self.current_playlist,
            Qt.MatchExactly
        )

        if items:
            self.playlist_list.setCurrentItem(
                items[0]
            )

        self.playlist_list.blockSignals(False)

    def refresh_tracks(self):
        self.track_list.clear()

        tracks = self.playlists.get(
            self.current_playlist,
            []
        )

        for track in tracks:
            self.track_list.addItem(
                self.label(track)
            )

    # ========================================================
    # ИНФОРМАЦИЯ
    # ========================================================

    def update_song_info(self, track):

        if not track:
            self.visualizer_title.setText(
                "Ничего не играет"
            )

            self.visualizer_artist.setText("")

            return

        title = (
            track.get("title")
            or
            "Без названия"
        )

        artist = (
            track.get("artist")
            or
            ""
        )

        self.visualizer_title.setText(title)
        self.visualizer_artist.setText(artist)

    def label(self, track):

        artist = track.get(
            "artist",
            ""
        )

        title = track.get(
            "title",
            "Без названия"
        )

        duration = track.get(
            "duration",
            0
        )

        if artist:
            text = f"{artist} — {title}"
        else:
            text = title

        if duration:
            text += (
                "  •  "
                +
                fmt_time(duration)
            )

        return text

    # ========================================================
    # ПЛЕЙЛИСТЫ
    # ========================================================

    def select_playlist(self, name):

        if not name:
            return

        self.current_playlist = name

        self.current_index = -1

        self.active_list = []
        self.play_order = []

        self.refresh_tracks()

    def create_playlist(self):

        name, ok = QInputDialog.getText(
            self,
            "Новый плейлист",
            "Название:"
        )

        if not ok:
            return

        name = name.strip()

        if not name:
            return

        if name in self.playlists:
            QMessageBox.warning(
                self,
                APP_NAME,
                "Плейлист с таким названием уже существует."
            )
            return

        self.playlists[name] = []

        self.current_playlist = name

        self.persist()

        self.refresh_playlists()
        self.refresh_tracks()

    def delete_playlist(self):

        if len(self.playlists) <= 1:
            QMessageBox.information(
                self,
                APP_NAME,
                "Нельзя удалить последний плейлист."
            )
            return

        answer = QMessageBox.question(
            self,
            "Удаление плейлиста",
            (
                f"Удалить плейлист "
                f"«{self.current_playlist}»?"
            ),
            QMessageBox.Yes |
            QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        del self.playlists[
            self.current_playlist
        ]

        self.current_playlist = next(
            iter(self.playlists)
        )

        self.persist()
        self.refresh_all()

    def playlist_context_menu(self, position):

        item = self.playlist_list.itemAt(
            position
        )

        if not item:
            return

        menu = QMenu(self)

        delete_action = QAction(
            "🗑 Удалить плейлист",
            self
        )

        delete_action.triggered.connect(
            self.delete_playlist
        )

        menu.addAction(delete_action)

        menu.exec_(
            self.playlist_list.mapToGlobal(
                position
            )
        )

    # ========================================================
    # ПЕСНИ
    # ========================================================

    def track_double_clicked(self, item):

        index = self.track_list.row(item)

        tracks = self.playlists[
            self.current_playlist
        ]

        self.play_from(
            index,
            tracks
        )

    def delete_track(self):

        row = self.track_list.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                APP_NAME,
                "Сначала выберите песню."
            )
            return

        tracks = self.playlists[
            self.current_playlist
        ]

        if not (
            0 <= row < len(tracks)
        ):
            return

        track = tracks[row]

        title = track.get(
            "title",
            "Без названия"
        )

        answer = QMessageBox.question(
            self,
            "Удаление песни",
            f"Удалить «{title}»?",
            QMessageBox.Yes |
            QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        if self.current_track is track:
            self.stop()

            self.current_track = None

            self.update_song_info(None)
            self.update_cover(None)

        del tracks[row]

        self.current_index = -1

        self.persist()
        self.refresh_tracks()

    def track_context_menu(self, position):

        item = self.track_list.itemAt(
            position
        )

        if not item:
            return

        row = self.track_list.row(item)

        menu = QMenu(self)

        play_action = QAction(
            "▶ Воспроизвести",
            self
        )

        play_action.triggered.connect(
            lambda:
            self.play_from(
                row,
                self.playlists[
                    self.current_playlist
                ]
            )
        )

        menu.addAction(play_action)

        delete_action = QAction(
            "🗑 Удалить",
            self
        )

        delete_action.triggered.connect(
            self.delete_track
        )

        menu.addAction(delete_action)

        menu.exec_(
            self.track_list.mapToGlobal(
                position
            )
        )

    # ========================================================
    # ФАЙЛЫ
    # ========================================================

    def add_files(self):

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Музыка",
            "",
            "Аудио (*.mp3 *.flac *.wav *.ogg *.m4a)"
        )

        if not files:
            return

        for path in files:

            track = {
                "title": Path(path).stem,
                "artist": "",
                "type": "local",
                "path": path,
                "cover": None,
                "duration": duration_of(path)
            }

            if HAS_MUTAGEN:
                try:
                    audio = MutagenFile(
                        path,
                        easy=True
                    )

                    if audio:

                        artists = audio.get(
                            "artist"
                        )

                        titles = audio.get(
                            "title"
                        )

                        if artists:
                            track["artist"] = artists[0]

                        if titles:
                            track["title"] = titles[0]

                except Exception:
                    pass

            self.playlists[
                self.current_playlist
            ].append(track)

            self.add_library(track)

        self.persist()
        self.refresh_tracks()

    # ========================================================
    # ССЫЛКА
    # ========================================================

    def add_link(self):

        url, ok = QInputDialog.getText(
            self,
            "Добавить ссылку",
            "URL трека:"
        )

        if not ok:
            return

        url = url.strip()

        if not url:
            return

        self.status.setText(
            "Получаю метаданные..."
        )

        self.worker = TrackWorker(url)

        self.worker.progress.connect(
            self.status.setText
        )

        self.worker.finished_ok.connect(
            self.link_done
        )

        self.worker.finished_err.connect(
            self.error
        )

        self.worker.start()

    def link_done(self, track):

        self.playlists[
            self.current_playlist
        ].append(track)

        self.add_library(track)

        self.persist()
        self.refresh_tracks()

        self.status.setText(
            "Трек добавлен."
        )

    # ========================================================
    # IMPORT
    # ========================================================

    def import_playlist(self):

        QMessageBox.information(
            self,
            APP_NAME,
            "Добавление отдельных ссылок уже работает.\n\n"
            "Полноценный импорт YouTube-плейлистов "
            "можно добавить отдельным модулем."
        )

    # ========================================================
    # LIBRARY
    # ========================================================

    def add_library(self, track):

        key = (
            track.get("path")
            or
            track.get("webpage_url")
            or
            track.get("title")
        )

        for item in self.library:

            item_key = (
                item.get("path")
                or
                item.get("webpage_url")
                or
                item.get("title")
            )

            if item_key == key:
                return

        self.library.append(
            dict(track)
        )

    # ========================================================
    # СОХРАНЕНИЕ
    # ========================================================

    def persist(self):

        save_playlists(
            self.playlists,
            self.library
        )

        save_settings(
            self.settings
        )

        save_themes(
            self.themes
        )

    # ========================================================
    # SHUFFLE
    # ========================================================

    def toggle_shuffle(self):

        self.settings["shuffle"] = not self.settings.get(
            "shuffle",
            False
        )

        if self.settings["shuffle"]:
            self.status.setText(
                "🔀 Перемешивание включено"
            )
        else:
            self.status.setText(
                "▶ Обычный порядок воспроизведения"
            )

        self.update_shuffle_button()
        self.persist()

    def update_shuffle_button(self):

        if not hasattr(
            self,
            "shuffle_button"
        ):
            return

        if self.settings.get(
            "shuffle",
            False
        ):
            self.shuffle_button.setText(
                "🔀 Перемешивание: ВКЛ"
            )

            self.shuffle_button.setObjectName(
                "shuffle"
            )

        else:
            self.shuffle_button.setText(
                "🔀 Перемешать"
            )

            self.shuffle_button.setObjectName("")

        self.shuffle_button.style().unpolish(
            self.shuffle_button
        )

        self.shuffle_button.style().polish(
            self.shuffle_button
        )

    def build_play_order(
        self,
        source,
        current_index
    ):

        if not source:
            return []

        indexes = list(
            range(len(source))
        )

        if self.settings.get(
            "shuffle",
            False
        ):
            random.shuffle(indexes)

            if (
                current_index in indexes
                and
                indexes[0] != current_index
            ):
                indexes.remove(current_index)
                indexes.insert(
                    0,
                    current_index
                )

        return indexes

    # ========================================================
    # PLAY
    # ========================================================

    def play_from(self, index, source):

        if not (
            0 <= index < len(source)
        ):
            return

        self.active_list = source

        self.play_order = self.build_play_order(
            source,
            index
        )

        if index in self.play_order:
            self.play_order.remove(index)

        self.play_order.insert(
            0,
            index
        )

        self.current_index = index

        self.play(source[index])

    def play(self, track):

        self.current_track = track

        self.track_title.setText(
            self.label(track)
        )

        self.update_song_info(track)
        self.update_cover(track)

        if track.get("type") == "local":

            try:
                pygame.mixer.music.load(
                    track["path"]
                )

                pygame.mixer.music.play()

                self.track_length = (
                    track.get("duration")
                    or
                    duration_of(track["path"])
                )

                track["duration"] = (
                    self.track_length
                )

                self.started()

            except Exception as e:
                self.error(
                    f"Не удалось открыть файл:\n{e}"
                )

        else:

            self.status.setText(
                "Получаю аудио..."
            )

            self.worker = ResolveWorker(track)

            self.worker.progress.connect(
                self.status.setText
            )

            self.worker.finished_ok.connect(
                self.resolved
            )

            self.worker.finished_err.connect(
                self.error
            )

            self.worker.start()

    def resolved(self, track, buffer):

        self.status.setText("")

        try:
            buffer.seek(0)

            pygame.mixer.music.load(buffer)
            pygame.mixer.music.play()

            self.current_track = track

            self.track_length = (
                track.get("duration")
                or
                0
            )

            self.update_song_info(track)
            self.update_cover(track)

            self.started()

        except Exception as e:
            self.error(
                f"Ошибка воспроизведения:\n{e}"
            )

    # ========================================================
    # STARTED
    # ========================================================

    def started(self):

        self.is_playing = True
        self.is_paused = False

        self.play_start_offset = 0
        self.play_started_at = time.time()

        self.play_button.setText("⏸")

        self.visualizer.set_active(True)

        self.total_time.setText(
            fmt_time(self.track_length)
        )

        self.current_time.setText("0:00")

        self.seek.setValue(0)

        self.update_cover(
            self.current_track
        )

        self.update_song_info(
            self.current_track
        )

    # ========================================================
    # ОБЛОЖКА
    # ========================================================

    def update_cover(self, track=None):

        path = ""

        if track:
            path = (
                track.get("cover")
                or
                ""
            )

        if not path:
            path = self.settings.get(
                "cover_path",
                ""
            )

        if (
            not path
            or
            not os.path.exists(path)
        ):
            self.cover.stop_movie()
            self.cover.setPixmap(QPixmap())
            self.cover.setText("Нет обложки")
            self.cover.update()
            return

        self.cover.set_animated_cover(path)

    # ========================================================
    # PLAY / PAUSE
    # ========================================================

    def toggle(self):

        if not self.current_track:

            tracks = self.playlists[
                self.current_playlist
            ]

            if tracks:
                self.play_from(
                    0,
                    tracks
                )

            return

        if (
            self.is_playing
            and
            not self.is_paused
        ):

            pygame.mixer.music.pause()

            self.is_paused = True

            self.play_button.setText("▶")

            self.visualizer.set_active(False)

            self.play_start_offset += (
                time.time()
                -
                self.play_started_at
            )

        elif self.is_paused:

            pygame.mixer.music.unpause()

            self.is_paused = False

            self.play_started_at = time.time()

            self.play_button.setText("⏸")

            self.visualizer.set_active(True)

    def stop(self):

        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        self.is_playing = False
        self.is_paused = False

        self.play_button.setText("▶")

        self.visualizer.set_active(False)

        self.seek.setValue(0)
        self.current_time.setText("0:00")

    # ========================================================
    # NEXT / PREVIOUS
    # ========================================================

    def next(self):

        source = (
            self.active_list
            or
            self.playlists.get(
                self.current_playlist,
                []
            )
        )

        if not source:
            return

        if not self.settings.get(
            "shuffle",
            False
        ):
            next_index = (
                self.current_index + 1
            ) % len(source)

        else:

            if not self.play_order:
                self.play_order = (
                    self.build_play_order(
                        source,
                        self.current_index
                    )
                )

            try:
                current_pos = (
                    self.play_order.index(
                        self.current_index
                    )
                )

            except ValueError:
                self.play_order = (
                    self.build_play_order(
                        source,
                        self.current_index
                    )
                )

                current_pos = 0

            next_pos = (
                current_pos + 1
            ) % len(self.play_order)

            next_index = (
                self.play_order[next_pos]
            )

        self.current_index = next_index

        self.play(
            source[next_index]
        )

    def prev(self):

        source = (
            self.active_list
            or
            self.playlists.get(
                self.current_playlist,
                []
            )
        )

        if not source:
            return

        if not self.settings.get(
            "shuffle",
            False
        ):
            prev_index = (
                self.current_index - 1
            ) % len(source)

        else:

            if not self.play_order:
                self.play_order = (
                    self.build_play_order(
                        source,
                        self.current_index
                    )
                )

            try:
                current_pos = (
                    self.play_order.index(
                        self.current_index
                    )
                )

            except ValueError:
                current_pos = 0

            prev_pos = (
                current_pos - 1
            ) % len(self.play_order)

            prev_index = (
                self.play_order[prev_pos]
            )

        self.current_index = prev_index

        self.play(
            source[prev_index]
        )

    # ========================================================
    # SEEK
    # ========================================================

    def seek_started(self):
        self.user_seeking = True

    def seek_released(self):

        self.user_seeking = False

        if (
            not self.current_track
            or
            self.track_length <= 0
        ):
            return

        position = (
            self.seek.value()
            /
            1000
            *
            self.track_length
        )

        self.do_seek(position)

    def do_seek(self, seconds):

        try:
            pygame.mixer.music.play(
                loops=0,
                start=float(seconds)
            )

            self.play_start_offset = float(seconds)
            self.play_started_at = time.time()

            self.is_playing = True
            self.is_paused = False

            self.play_button.setText("⏸")

            self.visualizer.set_active(True)

        except Exception:
            self.status.setText(
                "Этот формат не поддерживает перемотку."
            )

    def jump(self, delta):

        if (
            not self.current_track
            or
            self.track_length <= 0
        ):
            return

        position = max(
            0,
            min(
                self.track_length - 0.1,
                self.current_position() + delta
            )
        )

        self.do_seek(position)

    def current_position(self):

        if (
            self.is_playing
            and
            not self.is_paused
        ):
            return (
                self.play_start_offset
                +
                (
                    time.time()
                    -
                    self.play_started_at
                )
            )

        return self.play_start_offset

    # ========================================================
    # PROGRESS
    # ========================================================

    def update_progress(self):

        try:

            if (
                not self.is_playing
                or
                self.is_paused
                or
                self.user_seeking
            ):
                return

            position = self.current_position()

            if (
                self.track_length > 0
                and
                position >= (
                    self.track_length - 0.15
                )
            ):
                self.next()
                return

            if not pygame.mixer.music.get_busy():

                if position < 1:
                    return

                if (
                    self.track_length <= 0
                    or
                    position >= (
                        self.track_length - 0.5
                    )
                ):
                    self.next()
                    return

            self.current_time.setText(
                fmt_time(position)
            )

            if self.track_length > 0:

                value = int(
                    max(
                        0,
                        min(
                            1,
                            position
                            /
                            self.track_length
                        )
                    )
                    *
                    1000
                )

                self.seek.blockSignals(True)

                self.seek.setValue(value)

                self.seek.blockSignals(False)

        except Exception as e:

            self.status.setText(
                f"Ошибка плеера: {e}"
            )

    # ========================================================
    # VOLUME
    # ========================================================

    def volume_changed(self, value):

        self.settings["volume"] = value

        try:
            pygame.mixer.music.set_volume(
                value / 100
            )
        except Exception:
            pass

        save_settings(
            self.settings
        )

    # ========================================================
    # SETTINGS
    # ========================================================

    def open_settings(self):

        dialog = SettingsDialog(
            self.settings,
            self.themes,
            self
        )

        if dialog.exec_() == QDialog.Accepted:

            self.settings = dialog.result()
            self.themes = dialog.themes

            save_settings(
                self.settings
            )

            save_themes(
                self.themes
            )

            # Применяем тему сразу.
            # Здесь также меняется title bar Windows.
            self.apply_appearance()

            self.status.setText(
                "Настройки сохранены."
            )

    # ========================================================
    # ERROR
    # ========================================================

    def error(self, message):

        self.status.setText("")

        QMessageBox.warning(
            self,
            APP_NAME,
            str(message)
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(self, event):

        self.persist()

        try:
            self.cover.stop_movie()
        except Exception:
            pass

        try:
            self.bg.stop_movie()
        except Exception:
            pass

        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass

        event.accept()


# ============================================================
# MAIN
# ============================================================

def main():

    app = QApplication(sys.argv)

    app.setApplicationName(
        APP_NAME
    )

    app.setApplicationDisplayName(
        APP_NAME
    )

    window = MainWindow()

    window.show()

    # Повторно применяем цвет после показа окна.
    # Это особенно полезно для Windows 11.
    set_windows_titlebar(
        window,
        window.settings
    )

    sys.exit(
        app.exec_()
    )


if __name__ == "__main__":
    main()