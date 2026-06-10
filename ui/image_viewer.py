from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QWheelEvent
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton,
                             QScrollArea, QVBoxLayout, QWidget, QSizePolicy)
from styles import apply_button_style


class _ZoomableScrollArea(QScrollArea):
    """QScrollArea يدعم التكبير/التصغير بعجلة الماوس مع Ctrl."""

    def __init__(self, viewer_dialog, parent=None):
        super().__init__(parent)
        self._viewer = viewer_dialog

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._viewer._zoom_in()
            elif delta < 0:
                self._viewer._zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)


class ImageViewerDialog(QDialog):
    def __init__(self, parent, image_path, title="معاينة الصورة"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(700, 520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._base_pixmap = QPixmap(image_path)
        self._zoom = 1.0
        self._fit_mode = True  # يبدأ بوضع ملائمة النافذة
        self._build()
        self._render()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        zoom_out_btn = QPushButton("➖ تصغير")
        apply_button_style(zoom_out_btn, "secondary")
        zoom_out_btn.clicked.connect(self._zoom_out)

        zoom_in_btn = QPushButton("➕ تكبير")
        apply_button_style(zoom_in_btn, "secondary")
        zoom_in_btn.clicked.connect(self._zoom_in)

        fit_btn = QPushButton("📐 ملائمة")
        apply_button_style(fit_btn, "primary")
        fit_btn.setToolTip("ملائمة الصورة لحجم النافذة")
        fit_btn.clicked.connect(self._fit_to_window)

        actual_btn = QPushButton("🔍 حجم طبيعي")
        apply_button_style(actual_btn, "warning")
        actual_btn.setToolTip("عرض الصورة بحجمها الأصلي (100%)")
        actual_btn.clicked.connect(self._actual_size)

        self.zoom_lbl = QLabel("100%")
        self.zoom_lbl.setStyleSheet(
            "color: #475569; font-weight: bold; font-size: 12px;"
            "background: #F1F5F9; border-radius: 6px; padding: 4px 10px;"
        )
        self.zoom_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_lbl.setFixedWidth(60)

        close_btn = QPushButton("إغلاق")
        apply_button_style(close_btn, "danger")
        close_btn.clicked.connect(self.accept)

        toolbar.addWidget(zoom_out_btn)
        toolbar.addWidget(zoom_in_btn)
        toolbar.addWidget(fit_btn)
        toolbar.addWidget(actual_btn)
        toolbar.addWidget(self.zoom_lbl)
        toolbar.addStretch()

        # معلومات الصورة
        if not self._base_pixmap.isNull():
            info = QLabel(
                f"📏 {self._base_pixmap.width()}×{self._base_pixmap.height()} بكسل"
            )
            info.setStyleSheet("color: #94A3B8; font-size: 11px;")
            toolbar.addWidget(info)

        toolbar.addWidget(close_btn)
        root.addLayout(toolbar)

        # تلميح الاستخدام
        hint = QLabel("💡 Ctrl + عجلة الماوس للتكبير/التصغير")
        hint.setStyleSheet("color: #94A3B8; font-size: 10px; padding: 0 4px;")
        root.addWidget(hint)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )

        wrap = QWidget()
        wrap_lay = QVBoxLayout(wrap)
        wrap_lay.setContentsMargins(0, 0, 0, 0)
        wrap_lay.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.scroll = _ZoomableScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(wrap)
        self.scroll.setStyleSheet(
            "QScrollArea { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; }"
        )
        root.addWidget(self.scroll)

    def _render(self):
        if self._base_pixmap.isNull():
            self.image_label.setText("تعذّر تحميل الصورة")
            return

        if self._fit_mode:
            # ملائمة الصورة لحجم منطقة العرض
            viewport = self.scroll.viewport().size()
            available_w = max(100, viewport.width() - 20)
            available_h = max(100, viewport.height() - 20)
            pix = self._base_pixmap.scaled(
                available_w, available_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            # حساب نسبة الزوم الفعلية
            self._zoom = pix.width() / max(1, self._base_pixmap.width())
        else:
            w = max(1, int(self._base_pixmap.width() * self._zoom))
            h = max(1, int(self._base_pixmap.height() * self._zoom))
            pix = self._base_pixmap.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        self.image_label.setPixmap(pix)
        self.zoom_lbl.setText(f"{self._zoom * 100:.0f}%")

    def _zoom_in(self):
        self._fit_mode = False
        self._zoom = min(5.0, self._zoom + 0.15)
        self._render()

    def _zoom_out(self):
        self._fit_mode = False
        self._zoom = max(0.1, self._zoom - 0.15)
        self._render()

    def _fit_to_window(self):
        self._fit_mode = True
        self._render()

    def _actual_size(self):
        self._fit_mode = False
        self._zoom = 1.0
        self._render()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._fit_mode:
            self._render()
