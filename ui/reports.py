from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
                             QFrame, QDateEdit, QGroupBox, QFormLayout, QDoubleSpinBox,
                             QTextEdit, QDialogButtonBox, QDialog, QMessageBox, QTabWidget)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from datetime import date, datetime
from styles import style_dialog_buttons, apply_button_style
from ui.feedback import notify_success


class ReportsWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 25, 30, 25)
        root.setSpacing(15)

        title = QLabel("التقارير والإحصائيات")
        title.setObjectName("page_title")
        root.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._revenue_tab(), "💰  الإيرادات")
        tabs.addTab(self._dresses_tab(), "👗  الفساتين")
        tabs.addTab(self._rentals_tab(), "📋  التأجيرات")
        root.addWidget(tabs)

    # ── Revenue Tab ──
    def _revenue_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setSpacing(15)

        # Summary cards
        cards = QHBoxLayout(); cards.setSpacing(10)
        self.cards_data = {}
        for key, label, color, icon in [
            ('today', 'إيرادات اليوم', '#5E8F7A', '💰'),
            ('month', 'إيرادات الشهر', '#7A6E8F', '📅'),
            ('pending', 'مبالغ معلقة', '#B8956B', '⏳'),
        ]:
            card = QFrame(); card.setObjectName("card"); card.setFixedHeight(100)
            cl = QVBoxLayout(card); cl.setContentsMargins(15, 10, 15, 10)
            icon_lbl = QLabel(f"{icon}  {label}")
            icon_lbl.setStyleSheet(f"color:{color}; font-weight:bold; font-size:13px;")
            val_lbl = QLabel("—")
            val_lbl.setStyleSheet(f"font-size:22px; font-weight:bold; color:{color};")
            cl.addWidget(icon_lbl); cl.addWidget(val_lbl)
            self.cards_data[key] = val_lbl
            cards.addWidget(card)
        lay.addLayout(cards)

        # Monthly breakdown
        month_grp = QGroupBox("إيرادات آخر 6 أشهر")
        mg = QVBoxLayout(month_grp)
        self.monthly_table = QTableWidget(0, 3)
        self.monthly_table.setHorizontalHeaderLabels(["الشهر", "الإيرادات", "عدد التأجيرات"])
        self.monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.monthly_table.setAlternatingRowColors(True)
        self.monthly_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.monthly_table.verticalHeader().setVisible(False)
        mg.addWidget(self.monthly_table)
        lay.addWidget(month_grp)
        return w

    # ── Dresses Tab ──
    def _dresses_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        grp = QGroupBox("أكثر الفساتين طلباً")
        gl = QVBoxLayout(grp)
        self.popular_table = QTableWidget(0, 4)
        self.popular_table.setHorizontalHeaderLabels(["الفستان", "الكود", "عدد مرات التأجير", "إجمالي الإيراد"])
        self.popular_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.popular_table.setAlternatingRowColors(True)
        self.popular_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.popular_table.verticalHeader().setVisible(False)
        gl.addWidget(self.popular_table)
        lay.addWidget(grp)
        return w

    # ── Rentals Tab ──
    def _rentals_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        # Filter
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("الشهر:"))
        self.month_filter = QComboBox()
        now = datetime.now()
        months = []
        for i in range(12):
            m = now.month - i
            y = now.year
            while m <= 0: m += 12; y -= 1
            months.append(f"{y}-{m:02d}")
        self.month_filter.addItems(months)
        self.month_filter.currentIndexChanged.connect(self.load_rentals_report)
        filter_row.addWidget(self.month_filter)
        filter_row.addStretch()
        lay.addLayout(filter_row)

        self.rentals_table = QTableWidget(0, 7)
        self.rentals_table.setHorizontalHeaderLabels(
            ["العميل", "الفستان", "تاريخ الاستلام", "موعد الإرجاع",
             "الإجمالي", "المدفوع", "المتبقي"])
        self.rentals_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rentals_table.setAlternatingRowColors(True)
        self.rentals_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.rentals_table.verticalHeader().setVisible(False)
        lay.addWidget(self.rentals_table)

        self.rentals_summary = QLabel("")
        self.rentals_summary.setStyleSheet(
            "color:#5C534D; font-weight:600; padding:10px 14px;"
            "background:#F5F0EA; border-radius:10px; border:1px solid #E8E0D6;"
        )
        lay.addWidget(self.rentals_summary)
        return w

    # ── Expenses Tab ──
    def _expenses_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setSpacing(10)

        # Add expense
        add_row = QHBoxLayout()
        add_btn = QPushButton("➕  إضافة مصروف")
        apply_button_style(add_btn, "primary")
        add_btn.clicked.connect(self._add_expense)
        add_row.addWidget(add_btn)
        add_row.addStretch()
        lay.addLayout(add_row)

        self.expenses_table = QTableWidget(0, 5)
        self.expenses_table.setHorizontalHeaderLabels(["التاريخ", "الوصف", "الفئة", "المبلغ", "ملاحظات"])
        self.expenses_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.expenses_table.setAlternatingRowColors(True)
        self.expenses_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.expenses_table.verticalHeader().setVisible(False)
        lay.addWidget(self.expenses_table)

        self.expenses_summary = QLabel("")
        self.expenses_summary.setStyleSheet(
            "color:#5C534D; font-weight:600; padding:10px 14px;"
            "background:#F5F0EA; border-radius:10px; border:1px solid #E8E0D6;"
        )
        lay.addWidget(self.expenses_summary)
        return w

    def load_data(self):
        stats = self.db.get_dashboard_stats()
        self.cards_data['today'].setText(f"{stats['today_revenue']:,.0f} جنيه")
        self.cards_data['month'].setText(f"{stats['monthly_revenue']:,.0f} جنيه")
        self.cards_data['pending'].setText(f"{stats['pending_payments']:,.0f} جنيه")

        # Monthly revenue
        monthly = self.db.get_monthly_revenue(6)
        self.monthly_table.setRowCount(0)
        for m in monthly:
            i = self.monthly_table.rowCount(); self.monthly_table.insertRow(i)
            month_str = m['month']
            try:
                y, mo = month_str.split('-')
                month_names = ['يناير','فبراير','مارس','أبريل','مايو','يونيو',
                               'يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر']
                month_ar = f"{month_names[int(mo)-1]} {y}"
            except:
                month_ar = month_str

            for col, v in enumerate([month_ar, f"{m['total']:,.0f} جنيه", "—"]):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.monthly_table.setItem(i, col, item)

        # Popular dresses
        popular = self.db.get_popular_dresses(10)
        self.popular_table.setRowCount(0)
        for d in popular:
            i = self.popular_table.rowCount(); self.popular_table.insertRow(i)
            for col, v in enumerate([d['name'], d['code'], str(d['cnt']), f"{d['revenue']:,.0f} جنيه"]):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.popular_table.setItem(i, col, item)

        self.load_rentals_report()

    def load_rentals_report(self):
        month = self.month_filter.currentText() if hasattr(self, 'month_filter') else None
        all_rentals = self.db.get_all_rentals()
        if month:
            rentals = [r for r in all_rentals if r['rental_date'].startswith(month)]
        else:
            rentals = all_rentals

        self.rentals_table.setRowCount(0)
        total_amount = total_paid = total_remaining = 0
        for r in rentals:
            i = self.rentals_table.rowCount(); self.rentals_table.insertRow(i)
            for col, v in enumerate([r['customer_name'], r['dress_name'],
                                      r['rental_date'], r['expected_return_date'],
                                      f"{r['total_amount']:,.0f} ج",
                                      f"{r['paid_amount']:,.0f} ج",
                                      f"{r['remaining_amount']:,.0f} ج"]):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.rentals_table.setItem(i, col, item)
            total_amount += r['total_amount']
            total_paid += r['paid_amount']
            total_remaining += r['remaining_amount']

        self.rentals_summary.setText(
            f"الإجمالي: {len(rentals)} تأجير  |  "
            f"إجمالي المبالغ: {total_amount:,.0f} ج  |  "
            f"المحصّل: {total_paid:,.0f} ج  |  "
            f"المعلق: {total_remaining:,.0f} ج"
        )

    def load_expenses(self):
        expenses = self.db.get_all_expenses()
        self.expenses_table.setRowCount(0)
        total = 0
        for e in expenses:
            i = self.expenses_table.rowCount(); self.expenses_table.insertRow(i)
            for col, v in enumerate([e['date'], e['description'], e['category'] or '—',
                                      f"{e['amount']:,.0f} ج", e['notes'] or '—']):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.expenses_table.setItem(i, col, item)
            total += e['amount']
        self.expenses_summary.setText(f"إجمالي المصروفات: {total:,.0f} جنيه  |  عدد العمليات: {len(expenses)}")

    def _add_expense(self):
        dlg = ExpenseDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            self.db.add_expense(**data)
            self.load_expenses()
            notify_success(self, f"تم تسجيل المصروف «{data['description']}» بنجاح.")


class ExpenseDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("إضافة مصروف")
        self.setMinimumWidth(400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        lay = QVBoxLayout(self)
        form = QFormLayout(); form.setSpacing(10)

        from PyQt6.QtWidgets import QLineEdit
        self.desc = QLineEdit()
        self.desc.setPlaceholderText("وصف المصروف")
        self.amount = QDoubleSpinBox(); self.amount.setRange(0, 999999)
        self.amount.setSuffix(" جنيه"); self.amount.setDecimals(0)
        self.category = QComboBox()
        self.category.addItems(["إيجار", "مرافق", "تنظيف", "صيانة", "رواتب", "شراء فساتين", "أخرى"])
        self.exp_date = QDateEdit(QDate.currentDate())
        self.exp_date.setCalendarPopup(True)
        self.exp_date.setDisplayFormat("yyyy-MM-dd")
        self.notes = QTextEdit(); self.notes.setMaximumHeight(60)

        form.addRow("الوصف *:", self.desc)
        form.addRow("المبلغ *:", self.amount)
        form.addRow("الفئة:", self.category)
        form.addRow("التاريخ:", self.exp_date)
        form.addRow("ملاحظات:", self.notes)
        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("حفظ")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        style_dialog_buttons(btns)
        lay.addWidget(btns)

    def _save(self):
        if not self.desc.text().strip() or self.amount.value() <= 0:
            QMessageBox.warning(self, "تنبيه", "يرجى ملء الوصف والمبلغ")
            return
        self.accept()

    def get_data(self):
        return {
            'description': self.desc.text().strip(),
            'amount': self.amount.value(),
            'category': self.category.currentText(),
            'exp_date': self.exp_date.date().toString("yyyy-MM-dd"),
            'notes': self.notes.toPlainText().strip() if hasattr(self.notes, 'toPlainText') else '',
        }
