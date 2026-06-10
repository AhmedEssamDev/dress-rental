# ثيم بوتيك فاخر — ألوان دافئة مع لمسة ذهبية
THEME_ACCENT = "#C9A86C"
THEME_ACCENT_LIGHT = "#E8D5B0"
THEME_PRIMARY = "#7D5A6A"
THEME_BG = "#F7F4F0"
THEME_TEXT = "#2C2428"
THEME_TEXT_MUTED = "#7A7268"

STAT_CARD_COLORS = {
    "available": "#5E8F7A",
    "active_rentals": "#6E7F9C",
    "overdue": "#C07878",
    "active_bookings": "#8A7A9E",
    "today_revenue": "#5E8F7A",
    "monthly_revenue": "#7A6E8F",
    "pending_payments": "#B8956B",
    "archived_total": "#8A8580",
}

BUTTON_STYLES = {
    "primary": """
        QPushButton {
            background-color: #7D5A6A;
            color: #FFFBF7;
            border: 1px solid #6B4A59;
            border-radius: 10px;
            padding: 11px 22px;
            font-weight: 600;
            font-size: 13px;
            min-height: 20px;
        }
        QPushButton:hover { background-color: #6B4A59; color: #FFFFFF; border-color: #5A3D4B; }
        QPushButton:pressed { background-color: #5A3D4B; color: #FFFFFF; }
        QPushButton:disabled { background-color: #D4C4CA; border-color: #D4C4CA; color: #F9F5F3; }
    """,
    "success": """
        QPushButton {
            background-color: #5A7D6E;
            color: #FFFFFF;
            border: 1px solid #4A6B5D;
            border-radius: 10px;
            padding: 11px 22px;
            font-weight: 600;
            min-height: 20px;
        }
        QPushButton:hover { background-color: #4A6B5D; color: #FFFFFF; }
        QPushButton:pressed { background-color: #3D5A4E; color: #FFFFFF; }
        QPushButton:disabled { background-color: #B8D4C8; border-color: #B8D4C8; color: #F5FAF7; }
    """,
    "danger": """
        QPushButton {
            background-color: #B85C5C;
            color: #FFFFFF;
            border: 1px solid #A04E4E;
            border-radius: 10px;
            padding: 11px 22px;
            font-weight: 600;
            min-height: 20px;
        }
        QPushButton:hover { background-color: #A04E4E; color: #FFFFFF; }
        QPushButton:pressed { background-color: #8A4242; color: #FFFFFF; }
        QPushButton:disabled { background-color: #E8C4C4; border-color: #E8C4C4; color: #FDF8F8; }
    """,
    "warning": """
        QPushButton {
            background-color: #A67C3D;
            color: #FFFFFF;
            border: 1px solid #8F6932;
            border-radius: 10px;
            padding: 11px 22px;
            font-weight: 600;
            min-height: 20px;
        }
        QPushButton:hover { background-color: #8F6932; color: #FFFFFF; }
        QPushButton:pressed { background-color: #7A5C2B; color: #FFFFFF; }
        QPushButton:disabled { background-color: #E8D4B0; border-color: #E8D4B0; color: #FFFBF5; }
    """,
    "secondary": """
        QPushButton {
            background-color: #4A4543;
            color: #F5F0EB;
            border: 1px solid #3A3634;
            border-radius: 10px;
            padding: 11px 22px;
            font-weight: 600;
            min-height: 20px;
        }
        QPushButton:hover { background-color: #3A3634; color: #FFFFFF; }
        QPushButton:pressed { background-color: #2C2927; color: #FFFFFF; }
        QPushButton:disabled { background-color: #C4BEB8; border-color: #C4BEB8; color: #F9F7F5; }
    """,
}


def apply_button_style(button, variant="primary"):
    """تطبيق لون مباشر على الزر (يعمل بشكل موثوق على Windows)."""
    from PyQt6.QtCore import Qt
    style = BUTTON_STYLES.get(variant, BUTTON_STYLES["primary"])
    button.setStyleSheet(style)
    button.setCursor(Qt.CursorShape.PointingHandCursor)


FORM_LABEL_STYLE = (
    f"color: {THEME_TEXT}; font-size: 14px; font-weight: 600;"
    "padding: 10px 6px; background: transparent;"
)
FORM_INPUT_STYLE = (
    f"background-color: #FFFFFF; color: {THEME_TEXT};"
    "border: 1.5px solid #DDD5CB; border-radius: 10px;"
    "padding: 10px 14px; font-size: 14px;"
)


def make_form_label(text):
    from PyQt6.QtWidgets import QLabel
    lbl = QLabel(text)
    lbl.setStyleSheet(FORM_LABEL_STYLE)
    lbl.setMinimumWidth(140)
    return lbl


def style_form_input(widget, min_height=40):
    widget.setMinimumHeight(min_height)
    widget.setStyleSheet(FORM_INPUT_STYLE)


RENTAL_DIALOG_STYLE = """
QDialog#new_rental_dialog {
    background-color: #F3EFE9;
}
QDialog#new_rental_dialog QLabel {
    color: #2C2428;
}
QDialog#new_rental_dialog QScrollArea {
    border: none;
    background: transparent;
}
QDialog#new_rental_dialog QWidget#scroll_content {
    background: transparent;
}
"""


def section_title_label(text, subtitle=""):
    from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
    from PyQt6.QtGui import QFont
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(2)
    t = QLabel(text)
    t.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
    t.setStyleSheet("color: #111827; background: transparent;")
    lay.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setStyleSheet("color: #6B7280; font-size: 12px; background: transparent;")
        lay.addWidget(s)
    return w


def make_rental_section_frame(accent_color="#7D5A6A"):
    from PyQt6.QtWidgets import QFrame
    frame = QFrame()
    frame.setObjectName("rental_section")
    frame.setStyleSheet(f"""
        QFrame#rental_section {{
            background-color: #FFFFFF;
            border: 1px solid #D1D5DB;
            border-radius: 12px;
            border-right: 5px solid {accent_color};
        }}
    """)
    return frame


def make_selection_chip():
    from PyQt6.QtWidgets import QLabel
    from PyQt6.QtCore import Qt
    lbl = QLabel("لم يتم الاختيار بعد")
    lbl.setWordWrap(True)
    lbl.setMinimumHeight(52)
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    lbl.setStyleSheet(
        "color: #6B7280; font-size: 13px; font-style: italic;"
        "background: #F9FAFB; border: 2px dashed #D1D5DB;"
        "border-radius: 10px; padding: 12px 16px;"
    )
    return lbl


def set_selection_chip(label, text):
    label.setText(text)
    label.setStyleSheet(
        "color: #065F46; font-size: 14px; font-weight: bold;"
        "background: #D1FAE5; border: 2px solid #6EE7B7;"
        "border-radius: 10px; padding: 12px 16px;"
    )


LIST_STYLE = """
    QListWidget {
        background: #FFFFFF;
        color: #111827;
        border: 2px solid #D1D5DB;
        border-radius: 10px;
        font-size: 14px;
        padding: 6px;
        outline: none;
    }
    QListWidget::item {
        padding: 10px 12px;
        border-radius: 6px;
        margin: 2px 4px;
    }
    QListWidget::item:selected {
        background: #7D5A6A;
        color: #FFFFFF;
    }
    QListWidget::item:hover {
        background: #EFF6FF;
        color: #111827;
    }
"""


def setup_form_layout(form):
    from PyQt6.QtCore import Qt
    form.setSpacing(14)
    form.setVerticalSpacing(18)
    form.setContentsMargins(14, 20, 14, 14)
    form.setLabelAlignment(
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    )
    form.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)


def style_dialog_buttons(button_box):
    """تطبيق ألوان واضحة على أزرار حوار الحفظ/الإلغاء."""
    from PyQt6.QtWidgets import QDialogButtonBox
    mapping = [
        (QDialogButtonBox.StandardButton.Save, "primary"),
        (QDialogButtonBox.StandardButton.Ok, "primary"),
        (QDialogButtonBox.StandardButton.Yes, "success"),
        (QDialogButtonBox.StandardButton.Cancel, "secondary"),
        (QDialogButtonBox.StandardButton.Close, "secondary"),
        (QDialogButtonBox.StandardButton.No, "secondary"),
    ]
    for role, variant in mapping:
        btn = button_box.button(role)
        if btn:
            apply_button_style(btn, variant)


MAIN_STYLE = """
QMainWindow {
    background-color: #F7F4F0;
    font-family: 'Segoe UI', 'Tahoma', Arial;
    font-size: 13px;
    color: #2C2428;
}
QStackedWidget {
    background-color: #F7F4F0;
}
QScrollArea {
    background: transparent;
    border: none;
}
QWidget {
    color: #2C2428;
}
QDialog {
    background-color: #FFFFFF;
    font-family: 'Segoe UI', Arial;
    font-size: 13px;
    color: #111827;
}
QDialog QLabel {
    color: #111827;
    background-color: transparent;
}
QDialog QGroupBox {
    background-color: #F3F4F6;
    border: 2px solid #D1D5DB;
    border-radius: 10px;
    margin-top: 16px;
    padding: 18px 14px 14px 14px;
    font-weight: bold;
    color: #111827;
}
QDialog QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 4px 12px;
    color: #7D5A6A;
    background-color: #F5F0EA;
    font-size: 14px;
    font-weight: bold;
}
QDialog QLineEdit, QDialog QComboBox, QDialog QTextEdit,
QDialog QSpinBox, QDialog QDoubleSpinBox, QDialog QDateEdit {
    background-color: #FFFFFF;
    color: #111827;
    border: 2px solid #9CA3AF;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    font-weight: normal;
    min-height: 30px;
    selection-background-color: #7D5A6A;
    selection-color: #FFFFFF;
}
QDialog QComboBox {
    color: #111827;
    border: 2px solid #9CA3AF;
    background-color: #FFFFFF;
    padding-right: 10px;
}
QDialog QComboBox:hover {
    color: #111827;
    border-color: #94A3B8;
    background-color: #F8FAFC;
}
QDialog QComboBox:focus,
QDialog QComboBox:on {
    color: #111827;
    border-color: #C9A86C;
    background-color: #FFFCF9;
}
QDialog QComboBox QAbstractItemView {
    color: #111827;
    background-color: #FFFFFF;
    border: 1px solid #E0D8CE;
    selection-background-color: #EDE4DC;
    selection-color: #2C2428;
}
QDialog QListWidget {
    background-color: #FFFFFF;
    color: #111827;
    border: 2px solid #D1D5DB;
    border-radius: 8px;
    font-size: 13px;
    padding: 4px;
}
QDialog QListWidget::item {
    color: #111827;
    padding: 6px 8px;
}
QDialog QListWidget::item:selected {
    background-color: #7D5A6A;
    color: #FFFFFF;
}
QDialog QListWidget::item:hover {
    background-color: #E5E7EB;
    color: #111827;
}

/* ── Sidebar ── */
#sidebar {
    background-color: #1F1B1E;
    min-width: 232px;
    max-width: 232px;
    border-left: 1px solid #2E282C;
}
#sidebar_logo_frame {
    background-color: #181416;
    padding: 8px;
    border-bottom: 1px solid #2E282C;
}
#sidebar_logo_icon {
    background: transparent;
}
#sidebar_shop_name {
    color: #F5EDE4;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 0.3px;
    background: transparent;
}
#sidebar_clock {
    color: #A89F96;
    font-size: 11px;
    background: transparent;
}
#sidebar_bottom_info {
    color: #7A7268;
    font-size: 10px;
    padding: 18px;
    background: transparent;
}
QPushButton#nav_btn {
    background-color: transparent;
    color: #C4BBB2;
    border: none;
    text-align: right;
    padding: 13px 20px;
    font-size: 13px;
    border-radius: 10px;
    margin: 3px 12px;
    font-weight: 500;
}
QPushButton#nav_btn:hover {
    background-color: #2A2528;
    color: #F0E8DF;
}
QPushButton#nav_btn:checked {
    background-color: #3A3236;
    color: #F5E6D3;
    border-right: 3px solid #C9A86C;
    font-weight: 600;
}
QPushButton#nav_btn:pressed {
    background-color: #322C30;
}

/* ── Cards ── */
QFrame#card {
    background-color: #FFFFFF;
    border-radius: 14px;
    border: 1px solid #E8E0D6;
}

/* ── Tables ── */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E8E0D6;
    border-radius: 12px;
    gridline-color: #F3EDE6;
    selection-background-color: #EDE4DC;
    selection-color: #2C2428;
    alternate-background-color: #FBF9F7;
    outline: none;
}
QTableWidget::item {
    padding: 11px 10px;
    border-bottom: 1px solid #F3EDE6;
    color: #3D3632;
}
QTableWidget::item:selected {
    background-color: #EDE4DC;
    color: #2C2428;
}
QHeaderView::section {
    background-color: #F5F0EA;
    color: #6B635C;
    font-weight: 600;
    font-size: 12px;
    padding: 12px 10px;
    border: none;
    border-bottom: 2px solid #E8E0D6;
}

/* ── Buttons ── */
QPushButton {
    background-color: #E5E7EB;
    color: #1F2937;
    border: 1px solid #D1D5DB;
    border-radius: 8px;
    padding: 11px 20px;
    font-weight: bold;
    font-size: 13px;
    min-height: 20px;
}
QPushButton:hover { background-color: #D1D5DB; color: #1F2937; border-color: #9CA3AF; }
QPushButton:pressed { background-color: #C7CDD8; color: #111827; border-color: #9CA3AF; }
QPushButton:focus { border: 2px solid #60A5FA; color: #1F2937; background-color: #DDE3EC; }
QPushButton:disabled {
    background-color: #E5E7EB;
    color: #9CA3AF;
    border-color: #E5E7EB;
}

QPushButton#btn_primary {
    background-color: #7D5A6A;
    color: #FFFFFF;
    border: 1px solid #6B4A59;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#btn_primary:hover { background-color: #6B4A59; color: #FFFFFF; }
QPushButton#btn_primary:pressed { background-color: #5A3D4B; color: #FFFFFF; }

QPushButton#btn_success {
    background-color: #5A7D6E;
    color: #FFFFFF;
    border: 1px solid #047857;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
}
QPushButton#btn_success:hover { background-color: #047857; color: #FFFFFF; }

QPushButton#btn_danger {
    background-color: #DC2626;
    color: #FFFFFF;
    border: 1px solid #B91C1C;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
}
QPushButton#btn_danger:hover { background-color: #B91C1C; color: #FFFFFF; }

QPushButton#btn_warning {
    background-color: #D97706;
    color: #FFFFFF;
    border: 1px solid #B45309;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
}
QPushButton#btn_warning:hover { background-color: #B45309; color: #FFFFFF; }

QPushButton#btn_secondary {
    background-color: #6B7280;
    color: #FFFFFF;
    border: 1px solid #4B5563;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
}
QPushButton#btn_secondary:hover { background-color: #4B5563; color: #FFFFFF; }

QDialogButtonBox QPushButton {
    min-width: 100px;
    min-height: 36px;
    color: #1F2937;
    background-color: #E5E7EB;
}
QDialogButtonBox QPushButton:hover {
    color: #1F2937;
    background-color: #D1D5DB;
}
QDialogButtonBox QPushButton:pressed {
    color: #111827;
    background-color: #C7CDD8;
}

/* ── Inputs ── */
QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: #FFFFFF;
    border: 1.8px solid #D1D5DB;
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 13px;
    color: #1A1F36;
    min-height: 22px;
}
QComboBox:hover {
    background-color: #F8FAFC;
    color: #1A1F36;
    border-color: #94A3B8;
}
QComboBox:focus {
    background-color: #FFFCF9;
    color: #1A1F36;
    border-color: #C9A86C;
}
QComboBox:on {
    background-color: #FFFCF9;
    color: #1A1F36;
    border-color: #C9A86C;
}
QComboBox:disabled {
    background-color: #F3F4F6;
    color: #6B7280;
    border-color: #D1D5DB;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QDateEdit:focus {
    border-color: #C9A86C;
    background-color: #FFFCF9;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
    background: transparent;
}
QComboBox::down-arrow { image: none; }
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #111827;
    border: 1px solid #CBD5E1;
    selection-background-color: #EDE4DC;
    selection-color: #2C2428;
    outline: none;
}
QComboBox QAbstractItemView::item {
    min-height: 28px;
    padding: 4px 8px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #F5F0EA;
    color: #2C2428;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #EDE4DC;
    color: #2C2428;
}

/* ── Labels ── */
QLabel#section_title {
    font-size: 18px;
    font-weight: 600;
    color: #2C2428;
    background: transparent;
}
QLabel#page_title {
    font-size: 26px;
    font-weight: 600;
    color: #2C2428;
    background: transparent;
    padding-bottom: 4px;
}
QLabel#page_subtitle {
    font-size: 12px;
    color: #7A7268;
    background: transparent;
}

/* ── Search bar ── */
QLineEdit#search_bar {
    background-color: #FFFFFF;
    border: 1.5px solid #E0D8CE;
    border-radius: 22px;
    padding: 10px 20px;
    font-size: 13px;
    color: #2C2428;
}
QLineEdit#search_bar:focus {
    border-color: #C9A86C;
    background-color: #FFFCF9;
}

/* ── Status badges ── */
QLabel#badge_available { color: #5E8F7A; background: #E8F2ED; border-radius:10px; padding:3px 12px; font-weight:600; font-size:11px; }
QLabel#badge_rented    { color: #6E7F9C; background: #ECEEF4; border-radius:10px; padding:3px 12px; font-weight:600; font-size:11px; }
QLabel#badge_overdue   { color: #C07878; background: #F8EDED; border-radius:10px; padding:3px 12px; font-weight:600; font-size:11px; }
QLabel#badge_returned  { color: #8A8580; background: #F0EEEB; border-radius:10px; padding:3px 12px; font-weight:600; font-size:11px; }

/* ── Tab Widget ── */
QTabWidget::pane {
    border: 1px solid #E8E0D6;
    border-radius: 12px;
    background: #FFFFFF;
    top: -1px;
}
QTabBar::tab {
    background: #EDE8E2;
    color: #7A7268;
    padding: 12px 22px;
    border-radius: 10px 10px 0 0;
    margin-left: 4px;
    font-weight: 500;
}
QTabBar::tab:hover {
    background: #E5DFD6;
    color: #4A4543;
}
QTabBar::tab:selected {
    background: #FFFFFF;
    color: #7D5A6A;
    font-weight: 600;
    border-bottom: 3px solid #C9A86C;
}

/* ── Scrollbar ── */
QScrollBar:vertical {
    border: none;
    background: #F0EBE4;
    width: 9px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #C9BFB4;
    border-radius: 4px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover { background: #A89F96; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; height: 0; }
QScrollBar:horizontal {
    border: none;
    background: #F0EBE4;
    height: 9px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #C9BFB4;
    border-radius: 4px;
    min-width: 28px;
}

/* ── GroupBox ── */
QGroupBox {
    font-weight: bold;
    color: #374151;
    border: 1.5px solid #E8EAF0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 0 10px;
    color: #7D5A6A;
}

/* ── MessageBox ── */
QMessageBox { background-color: white; }
QMessageBox QPushButton { min-width: 80px; }
"""

STATUS_AR = {
    'available': 'متاح',
    'rented': 'مؤجر',
    'maintenance': 'صيانة',
    'active': 'نشط',
    'overdue': 'متأخر',
    'returned': 'مُرجع',
    'cancelled': 'ملغي',
    'converted': 'تم التحويل',
    'cash': 'كاش',
    'card': 'بطاقة',
    'transfer': 'تحويل',
}

STATUS_COLOR = {
    'available': '#5E8F7A',
    'rented': '#6E7F9C',
    'maintenance': '#A67C3D',
    'active': '#5E8F7A',
    'overdue': '#C07878',
    'returned': '#8A8580',
    'cancelled': '#A89F96',
    'converted': '#8A7A9E',
}
