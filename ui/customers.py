from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
                             QDialog, QFormLayout, QTextEdit, QMessageBox, QDialogButtonBox,
                             QTabWidget, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from styles import STATUS_AR, STATUS_COLOR, style_dialog_buttons, apply_button_style
from ui.feedback import after_save, notify_success
from ui.admin_auth import AdminAuthDialog


class CustomerDialog(QDialog):
    def __init__(self, parent, customer=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("إضافة عميل" if not customer else "تعديل بيانات العميل")
        self.setMinimumWidth(420)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build()
        if customer:
            self._fill(customer)

    def _build(self):
        lay = QVBoxLayout(self)
        form = QFormLayout(); form.setSpacing(10)

        self.name = QLineEdit(); self.name.setPlaceholderText("الاسم الكامل")
        self.phone = QLineEdit(); self.phone.setPlaceholderText("01xxxxxxxxx")
        self.phone2 = QLineEdit(); self.phone2.setPlaceholderText("رقم بديل (اختياري)")
        self.id_number = QLineEdit(); self.id_number.setPlaceholderText("رقم الهوية الوطنية")
        self.address = QLineEdit(); self.address.setPlaceholderText("العنوان")
        self.notes = QTextEdit(); self.notes.setMaximumHeight(70)
        self.notes.setPlaceholderText("ملاحظات...")

        form.addRow("الاسم *:", self.name)
        form.addRow("الهاتف *:", self.phone)
        form.addRow("هاتف 2:", self.phone2)
        form.addRow("رقم الهوية:", self.id_number)
        form.addRow("العنوان:", self.address)
        form.addRow("ملاحظات:", self.notes)
        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        save_lbl = "حفظ التعديلات" if self.customer else "حفظ"
        btns.button(QDialogButtonBox.StandardButton.Save).setText(save_lbl)
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        style_dialog_buttons(btns)
        lay.addWidget(btns)

    def _fill(self, c):
        self.name.setText(c['name'])
        self.phone.setText(c['phone'] or '')
        self.phone2.setText(c['phone2'] or '')
        self.id_number.setText(c['id_number'] or '')
        self.address.setText(c['address'] or '')
        self.notes.setPlainText(c['notes'] or '')

    def _save(self):
        if not self.name.text().strip() or not self.phone.text().strip():
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال الاسم ورقم الهاتف")
            return
        self.accept()

    def get_data(self):
        return {
            'name': self.name.text().strip(),
            'phone': self.phone.text().strip(),
            'phone2': self.phone2.text().strip(),
            'address': self.address.text().strip(),
            'id_number': self.id_number.text().strip(),
            'notes': self.notes.toPlainText().strip(),
        }


class CustomersWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_page = 1
        self.items_per_page = 50
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 25, 30, 25)
        root.setSpacing(15)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("إدارة العملاء")
        title.setObjectName("page_title")
        hdr.addWidget(title)
        hdr.addStretch()
        add_btn = QPushButton("➕  إضافة عميل جديد")
        apply_button_style(add_btn, "primary")
        add_btn.clicked.connect(self.add_customer)
        hdr.addWidget(add_btn)
        root.addLayout(hdr)

        # Search
        self.search = QLineEdit()
        self.search.setObjectName("search_bar")
        self.search.setPlaceholderText("🔍  بحث بالاسم أو الهاتف أو رقم الهوية...")
        self.search.setFixedWidth(350)
        self.search.textChanged.connect(self.load_data)
        root.addWidget(self.search)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["الاسم", "الهاتف", "هاتف 2",
                                               "رقم الهوية", "العنوان", "تاريخ التسجيل"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(lambda: self.edit_customer())
        root.addWidget(self.table)

        # Actions
        action = QHBoxLayout(); action.setSpacing(10)
        edit_btn = QPushButton("✏️  تعديل")
        apply_button_style(edit_btn, "warning")
        edit_btn.clicked.connect(self.edit_customer)
        del_btn = QPushButton("🗑️  حذف")
        apply_button_style(del_btn, "danger")
        del_btn.clicked.connect(self.archive_customer)
        hist_btn = QPushButton("📋  سجل التأجيرات")
        apply_button_style(hist_btn, "secondary")
        hist_btn.clicked.connect(self.view_customer_history)
        action.addWidget(edit_btn)
        action.addWidget(del_btn)
        action.addWidget(hist_btn)
        action.addStretch()
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color:#6B7280; font-size:12px;")
        action.addWidget(self.count_lbl)
        root.addLayout(action)

        # Pagination
        pag_lay = QHBoxLayout()
        self.prev_btn = QPushButton("◀ السابق")
        self.next_btn = QPushButton("التالي ▶")
        self.page_lbl = QLabel("صفحة 1")
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        pag_lay.addStretch()
        pag_lay.addWidget(self.prev_btn)
        pag_lay.addWidget(self.page_lbl)
        pag_lay.addWidget(self.next_btn)
        pag_lay.addStretch()
        root.addLayout(pag_lay)

        self.customer_ids = []

    def load_data(self):
        search = self.search.text().strip() or None
        
        offset = (self.current_page - 1) * self.items_per_page
        rows = self.db.get_all_customers(search=search, limit=self.items_per_page, offset=offset)
        total_count = self.db.get_customers_count(search=search)
        
        self.table.setRowCount(0)
        self.customer_ids = []
        for c in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.customer_ids.append(c['id'])
            vals = [c['name'], c['phone'] or '—', c['phone2'] or '—',
                    c['id_number'] or '—', c['address'] or '—',
                    c['created_at'][:10] if c['created_at'] else '—']
            for col, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, col, item)
                
        total_pages = (total_count + self.items_per_page - 1) // self.items_per_page
        if total_pages == 0: total_pages = 1
        self.page_lbl.setText(f"صفحة {self.current_page} من {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)
        self.count_lbl.setText(f"إجمالي: {total_count} عميل")

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def next_page(self):
        self.current_page += 1
        self.load_data()

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.customer_ids):
            return None
        return self.customer_ids[row]

    def add_customer(self):
        dlg = CustomerDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            cid = self.db.add_customer(**data)
            self.load_data()
            row = next((i for i, x in enumerate(self.customer_ids) if x == cid), -1)
            after_save(self, self.table, row, f"تم إضافة العميل «{data['name']}» بنجاح.")

    def edit_customer(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار عميل أولاً")
            return
        customer = self.db.get_customer(cid)
        dlg = CustomerDialog(self, customer)
        if dlg.exec():
            data = dlg.get_data()
            self.db.update_customer(cid, **data)
            self.load_data()
            row = next((i for i, x in enumerate(self.customer_ids) if x == cid), -1)
            after_save(self, self.table, row, f"تم تحديث بيانات العميل «{data['name']}» بنجاح.")

    def archive_customer(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار عميل أولاً")
            return
        customer = self.db.get_customer(cid)
        reply = QMessageBox.question(self, "تأكيد الحذف",
                                     f"هل أنت متأكد أنك تريد حذف العميل «{customer['name']}»؟\n\n"
                                     "ملاحظة: سيتم حذف العميل من القوائم فقط\nولن يتم إتلاف بياناته المرتبطة بالفواتير والتأجيرات.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if not AdminAuthDialog(self, self.db).exec():
                return
            ok, err = self.db.archive_customer(cid)
            if not ok:
                QMessageBox.warning(self, "تعذر الحذف", err or "لا يمكن حذف العميل حالياً")
                return
            self.load_data()

    def view_customer_history(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار عميل أولاً")
            return
        customer = self.db.get_customer(cid)
        dlg = CustomerHistoryDialog(self, self.db, customer)
        dlg.exec()


class CustomerHistoryDialog(QDialog):
    def __init__(self, parent, db, customer):
        super().__init__(parent)
        self.setWindowTitle(f"سجل العميل: {customer['name']}")
        self.setMinimumSize(700, 500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        lay = QVBoxLayout(self)

        info = QLabel(f"👤  {customer['name']}   |   📞  {customer['phone'] or '—'}"
                      f"   |   🪪  {customer['id_number'] or '—'}")
        info.setStyleSheet("font-size:14px; font-weight:bold; color:#374151; padding:10px; "
                           "background:#F0F2F5; border-radius:8px;")
        lay.addWidget(info)

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(["الفستان", "تاريخ الاستلام", "موعد الإرجاع",
                                          "السعر", "المدفوع", "الحالة"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)

        rentals = [r for r in db.get_all_rentals() if r['customer_id'] == customer['id']]
        total_paid = 0
        for r in rentals:
            i = table.rowCount(); table.insertRow(i)
            st = r['status']
            vals = [r['dress_name'], r['rental_date'], r['expected_return_date'],
                    f"{r['total_amount']:,.0f} ج", f"{r['paid_amount']:,.0f} ج",
                    STATUS_AR.get(st, st)]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 5:
                    item.setForeground(QColor(STATUS_COLOR.get(st, '#000')))
                table.setItem(i, col, item)
            total_paid += r['paid_amount']

        lay.addWidget(table)
        summary = QLabel(f"إجمالي التأجيرات: {len(rentals)}  |  إجمالي المدفوع: {total_paid:,.0f} جنيه")
        summary.setStyleSheet("color:#6B7280; font-size:12px; padding:8px;")
        lay.addWidget(summary)

        close_btn = QPushButton("إغلاق")
        apply_button_style(close_btn, "secondary")
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignLeft)
