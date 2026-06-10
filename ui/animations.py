from PyQt6.QtCore import QObject, QEvent, QEasingCurve, QPropertyAnimation, pyqtProperty, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QLineEdit, QTextEdit, QWidget


class SpinRefreshIcon(QWidget):
    """أيقونة سهم دائري تدور عند التحديث."""

    def __init__(self, parent=None, size=18, color="#FFFFFF"):
        super().__init__(parent)
        self._angle = 0.0
        self._color = QColor(color)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        self._anim = None

    def get_angle(self):
        return self._angle

    def set_angle(self, value):
        self._angle = float(value) % 360.0
        self.update()

    angle = pyqtProperty(float, get_angle, set_angle)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)
        p.rotate(self._angle)

        pen = QPen(self._color, 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        r = min(self.width(), self.height()) / 2 - 2
        # قوس دائري (سهم التحديث)
        p.drawArc(int(-r), int(-r), int(2 * r), int(2 * r), 50 * 16, 260 * 16)
        # رأس السهم
        p.drawLine(int(r * 0.55), int(-r * 0.75), int(r * 0.9), int(-r * 0.35))
        p.drawLine(int(r * 0.55), int(-r * 0.75), int(r * 0.15), int(-r * 0.45))

    def start_spin(self):
        if self._anim and self._anim.state() == QPropertyAnimation.State.Running:
            return
        self._anim = QPropertyAnimation(self, b"angle", self)
        self._anim.setDuration(700)
        self._anim.setStartValue(self._angle)
        self._anim.setEndValue(self._angle + 360)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.Type.Linear)
        self._anim.start()

    def stop_spin(self):
        if self._anim:
            self._anim.stop()
            self._anim = None
        self.set_angle(0)


class UIAnimator(QObject):
    """Adds subtle hover/focus animations globally."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._animations = {}

    def eventFilter(self, obj, event):
        if not isinstance(obj, QWidget):
            return False

        et = event.type()
        if isinstance(obj, (QLineEdit, QTextEdit)):
            # استثناء حقول البحث — لديها تأثيرات CSS خاصة بها
            # تطبيق QGraphicsDropShadowEffect عليها يتسبب في اختفائها داخل QScrollArea
            if getattr(obj, 'objectName', lambda: '')() == 'search_bar':
                return False
            if et == QEvent.Type.FocusIn:
                self._animate_shadow(obj, blur=14.0, alpha=70, duration=120, color="#3B82F6")
            elif et == QEvent.Type.FocusOut:
                self._animate_shadow(obj, blur=0.0, alpha=0, duration=120, color="#3B82F6")

        return False

    def _ensure_shadow(self, widget: QWidget):
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsDropShadowEffect):
            effect = QGraphicsDropShadowEffect(widget)
            effect.setBlurRadius(0.0)
            effect.setOffset(0, 0)
            effect.setColor(QColor(0, 0, 0, 0))
            widget.setGraphicsEffect(effect)
        return effect

    def _animate_shadow(self, widget: QWidget, blur: float, alpha: int, duration: int, color: str = "#1F2937"):
        effect = self._ensure_shadow(widget)
        target = QColor(color)
        target.setAlpha(max(0, min(alpha, 255)))

        blur_anim = QPropertyAnimation(effect, b"blurRadius", self)
        blur_anim.setDuration(duration)
        blur_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        blur_anim.setStartValue(effect.blurRadius())
        blur_anim.setEndValue(blur)
        blur_anim.start()

        color_anim = QPropertyAnimation(effect, b"color", self)
        color_anim.setDuration(duration)
        color_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        color_anim.setStartValue(effect.color())
        color_anim.setEndValue(target)
        color_anim.start()

        self._animations[(id(widget), "blur")] = blur_anim
        self._animations[(id(widget), "color")] = color_anim


def install_global_animations(app, root_widget):
    animator = UIAnimator(parent=root_widget)
    app.installEventFilter(animator)

    for w in root_widget.findChildren(QWidget):
        if isinstance(w, (QLineEdit, QTextEdit)):
            w.installEventFilter(animator)
    return animator
