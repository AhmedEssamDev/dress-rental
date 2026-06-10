from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
from styles import STATUS_AR, apply_button_style, STAT_CARD_COLORS, THEME_TEXT_MUTED
from ui.feedback import notify_success
from ui.animations import SpinRefreshIcon


def make_stat_card(title, value, subtitle, color, icon):
    card = QFrame()
    card.setObjectName("card")
    card.setFixedHeight(128)
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(18, 16, 18, 14)
    lay.setSpacing(6)

    top = QHBoxLayout()
    icon_lbl = QLabel(icon)
    icon_lbl.setFont(QFont("Segoe UI Emoji", 20))
    icon_lbl.setFixedSize(44, 44)
    icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_lbl.setStyleSheet(
        f"background: {color}18; border: 1px solid {color}35;"
        f"border-radius: 14px; color: {color};"
    )

    val_lbl = QLabel(str(value))
    val_lbl.setStyleSheet(
        f"font-size: 26px; font-weight: 600; color: {color}; background: transparent;"
    )
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    top.addWidget(icon_lbl)
    top.addStretch()
    top.addWidget(val_lbl)
    lay.addLayout(top)

    t = QLabel(title)
    t.setStyleSheet(
        f"font-size: 13px; font-weight: 600; color: #3D3632; background: transparent;"
    )
    s = QLabel(subtitle)
    s.setStyleSheet(
        f"font-size: 11px; color: {THEME_TEXT_MUTED}; background: transparent;"
    )
    lay.addWidget(t)
    lay.addWidget(s)
    return card, val_lbl


class DashboardWidget(QWidget):
    def __init__(self, db, switch_fn=None):
        super().__init__()
        self.db = db
        self.switch_fn = switch_fn
        self.stat_labels = {}
        self._build_ui()
        self.refresh()

        # Auto-refresh every 60 seconds
        timer = QTimer(self)
        timer.timeout.connect(self.refresh)
        timer.start(60000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 25, 30, 25)
        root.setSpacing(14)

        # Title
        hdr = QHBoxLayout()
        title = QLabel("لوحة التحكم")
        title.setObjectName("page_title")
        hdr.addWidget(title)
        hdr.addStretch()
        self.last_updated_lbl = QLabel("")
        self.last_updated_lbl.setStyleSheet(
            f"font-size:11px; color:{THEME_TEXT_MUTED}; background:transparent;"
        )
        hdr.addWidget(self.last_updated_lbl)
        self.refresh_btn = QPushButton()
        apply_button_style(self.refresh_btn, "secondary")
        self.refresh_btn.setStyleSheet(
            self.refresh_btn.styleSheet()
            + """
            QLabel {
                background: transparent;
                color: #FFFFFF;
                border: none;
                font-weight: bold;
            }
            """
        )
        self.refresh_btn.setFixedWidth(100)
        refresh_lay = QHBoxLayout(self.refresh_btn)
        refresh_lay.setContentsMargins(8, 0, 10, 0)
        refresh_lay.setSpacing(5)
        self.refresh_icon = SpinRefreshIcon(self.refresh_btn, size=16, color="#FFFFFF")
        self.refresh_label = QLabel("تحديث")
        refresh_lay.addWidget(self.refresh_icon)
        refresh_lay.addWidget(self.refresh_label)
        self.refresh_btn.clicked.connect(lambda: self.refresh(show_feedback=True))
        hdr.addWidget(self.refresh_btn)
        root.addLayout(hdr)

        summary = QLabel("ملخص سريع: أهم الأرقام والتنبيهات القادمة")
        summary.setObjectName("page_subtitle")
        root.addWidget(summary)

        # Simplified KPIs
        row1 = QHBoxLayout(); row1.setSpacing(14)
        c, l = make_stat_card("فساتين متاحة", "—", "جاهزة للتأجير",
                              STAT_CARD_COLORS["available"], "✅")
        self.stat_labels['available'] = l; row1.addWidget(c)
        c.setCursor(Qt.CursorShape.PointingHandCursor)
        c.mousePressEvent = lambda e: self.switch_fn(1) if self.switch_fn else None

        c, l = make_stat_card("تأجيرات نشطة", "—", "نشطة + متأخرة",
                              STAT_CARD_COLORS["active_rentals"], "📦")
        self.stat_labels['active_rentals'] = l; row1.addWidget(c)
        c.setCursor(Qt.CursorShape.PointingHandCursor)
        c.mousePressEvent = lambda e: self.switch_fn(5) if self.switch_fn else None

        c, l = make_stat_card("تأجيرات متأخرة", "—", "تحتاج متابعة",
                              STAT_CARD_COLORS["overdue"], "⚠️")
        self.stat_labels['overdue'] = l; row1.addWidget(c)
        c.setCursor(Qt.CursorShape.PointingHandCursor)
        c.mousePressEvent = lambda e: self.switch_fn(5) if self.switch_fn else None

        c, l = make_stat_card("الحجوزات النشطة", "—", "أحداث قادمة",
                              STAT_CARD_COLORS["active_bookings"], "📅")
        self.stat_labels['active_bookings'] = l; row1.addWidget(c)
        c.setCursor(Qt.CursorShape.PointingHandCursor)
        c.mousePressEvent = lambda e: self.switch_fn(3) if self.switch_fn else None
        root.addLayout(row1)

        row2 = QHBoxLayout(); row2.setSpacing(14)
        c, l = make_stat_card("إيراد اليوم", "—", "جنيه",
                              STAT_CARD_COLORS["today_revenue"], "💵")
        self.stat_labels['today_revenue'] = l; row2.addWidget(c)
        c, l = make_stat_card("إيراد الشهر", "—", "جنيه",
                              STAT_CARD_COLORS["monthly_revenue"], "📈")
        self.stat_labels['monthly_revenue'] = l; row2.addWidget(c)
        c, l = make_stat_card("مبالغ معلقة", "—", "غير محصلة",
                              STAT_CARD_COLORS["pending_payments"], "⏳")
        self.stat_labels['pending_payments'] = l; row2.addWidget(c)
        root.addLayout(row2)

        # Two clear tables only
        bottom = QHBoxLayout(); bottom.setSpacing(12)
        bottom.addWidget(self._build_alerts_card(), 1)
        bottom.addWidget(self._build_bookings_card(), 1)
        root.addLayout(bottom)

    def _build_alerts_card(self):
        card = QFrame(); card.setObjectName("card")
        lay = QVBoxLayout(card); lay.setContentsMargins(20, 15, 20, 15); lay.setSpacing(10)

        hdr = QHBoxLayout()
        t = QLabel("⚠️  تنبيهات الإرجاع المتأخر")
        t.setStyleSheet("font-size:15px; font-weight:600; color:#B85C5C; background:transparent;")
        hdr.addWidget(t); hdr.addStretch()
        lay.addLayout(hdr)

        self.overdue_table = self._make_table(["العميل", "الفستان", "موعد الإرجاع", "الهاتف"])
        lay.addWidget(self.overdue_table)
        return card

    def _make_table(self, headers):
        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.setAlternatingRowColors(True)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tbl.verticalHeader().setVisible(False)
        tbl.setMaximumHeight(220)
        return tbl

    def _build_bookings_card(self):
        card = QFrame(); card.setObjectName("card")
        lay = QVBoxLayout(card); lay.setContentsMargins(20, 15, 20, 15); lay.setSpacing(10)
        t = QLabel("📅  الحجوزات خلال 7 أيام")
        t.setStyleSheet("font-size:15px; font-weight:600; color:#8A7A9E; background:transparent;")
        lay.addWidget(t)
        self.bookings_table = self._make_table(["العميل", "الفستان", "المسجّل", "تاريخ المناسبة", "الهاتف"])
        self.bookings_table.doubleClicked.connect(self._open_bookings_page)
        lay.addWidget(self.bookings_table)
        self.bookings_hint = QLabel("")
        self.bookings_hint.setStyleSheet("font-size:12px; color:#6B7280;")
        lay.addWidget(self.bookings_hint)
        return card

    def refresh(self, show_feedback=False):
        if show_feedback:
            self.refresh_btn.setEnabled(False)
            self.refresh_label.setText("جاري التحديث…")
            self.refresh_icon.start_spin()

        self.db.update_overdue_status()
        stats = self.db.get_dashboard_stats()
        d = stats.get('dresses', {})
        available = d.get('available', 0)
        active_rentals = stats.get('active_rentals', 0)
        overdue_count = stats.get('overdue_rentals', 0)
        today_revenue = stats.get('today_revenue', 0)
        monthly_revenue = stats.get('monthly_revenue', 0)
        pending = stats.get('pending_payments', 0)
        active_bookings = stats.get('active_bookings', 0)

        self.stat_labels['available'].setText(str(available))
        self.stat_labels['active_rentals'].setText(str(active_rentals))
        self.stat_labels['overdue'].setText(str(overdue_count))
        self.stat_labels['today_revenue'].setText(f"{today_revenue:,.0f}")
        self.stat_labels['monthly_revenue'].setText(f"{monthly_revenue:,.0f}")
        self.stat_labels['pending_payments'].setText(f"{pending:,.0f}")
        self.stat_labels['active_bookings'].setText(str(active_bookings))

        # Overdue table
        overdue = self.db.get_overdue_rentals()
        self._fill_table(self.overdue_table, overdue, "#FEF2F2")

        # Upcoming bookings table
        bookings = self.db.get_upcoming_bookings(7)
        self._fill_bookings_table(bookings)
        near_bookings = self.db.get_upcoming_bookings(2)
        if near_bookings:
            self.bookings_hint.setText(f"🔔 لديك {len(near_bookings)} حجز خلال يومين")
            self.bookings_hint.setStyleSheet("font-size:12px; color:#B45309; font-weight:bold;")
        else:
            self.bookings_hint.setText("لا توجد حجوزات خلال يومين")
            self.bookings_hint.setStyleSheet("font-size:12px; color:#6B7280;")

        now = datetime.now().strftime("%H:%M:%S")
        self.last_updated_lbl.setText(f"آخر تحديث: {now}")

        if show_feedback:
            summary = (
                "تم تحديث لوحة التحكم بنجاح.\n\n"
                f"• فساتين متاحة: {available}\n"
                f"• تأجيرات نشطة: {active_rentals}\n"
                f"• تأجيرات متأخرة: {overdue_count}\n"
                f"• حجوزات نشطة: {active_bookings}\n"
                f"• حجوزات خلال 7 أيام: {len(bookings)}\n"
                f"• إيراد اليوم: {today_revenue:,.0f} ج\n"
                f"• مبالغ معلقة: {pending:,.0f} ج"
            )
            QTimer.singleShot(500, lambda: self._finish_refresh_ui(summary))

    def _finish_refresh_ui(self, summary: str):
        self.refresh_icon.stop_spin()
        self.refresh_label.setText("تحديث")
        self.refresh_btn.setEnabled(True)
        notify_success(self, summary, title="تم التحديث ✅")

    def _fill_table(self, table, rows, bg):
        table.setRowCount(0)
        for r in rows:
            i = table.rowCount()
            table.insertRow(i)
            for col, val in enumerate([r['customer_name'], r['dress_name'],
                                       r['expected_return_date'], r['customer_phone'] or '—']):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QColor(bg))
                table.setItem(i, col, item)
        if table.rowCount() == 0:
            table.setRowCount(1)
            item = QTableWidgetItem("لا توجد سجلات")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setForeground(QColor("#9CA3AF"))
            table.setItem(0, 0, item)
            table.setSpan(0, 0, 1, 4)

    def _fill_bookings_table(self, rows):
        self.bookings_table.setRowCount(0)
        for r in rows:
            i = self.bookings_table.rowCount()
            self.bookings_table.insertRow(i)
            for col, val in enumerate([
                r['customer_name'], r['dress_name'], r['registrar_name'] or '—',
                r['event_date'], r['customer_phone'] or '—',
            ]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QColor("#F5F3FF"))
                self.bookings_table.setItem(i, col, item)
        if self.bookings_table.rowCount() == 0:
            self.bookings_table.setRowCount(1)
            item = QTableWidgetItem("لا توجد حجوزات قريبة")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setForeground(QColor("#9CA3AF"))
            self.bookings_table.setItem(0, 0, item)
            self.bookings_table.setSpan(0, 0, 1, 5)

    def _open_bookings_page(self):
        if self.switch_fn:
            self.switch_fn(3)
