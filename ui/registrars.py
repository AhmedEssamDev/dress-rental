from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
                             QDialog, QFormLayout, QTextEdit, QMessageBox, QDialogButtonBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from styles import style_dialog_buttons, apply_button_style
from ui.feedback import after_save, notify_success
from ui.admin_auth import AdminAuthDialog


class RegistrarDialog(QDialog):
    def __init__(self, parent, registrar=None):
        super().__init__(parent)
        self.registrar = registrar
        self.setWindowTitle("إضافة مسجّل" if not registrar else "تعديل بيانات المسجّل")
        self.setMinimumWidth(400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build()
        if registrar:
            self._fill(registrar)

    def _build(self):
        lay = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.name = QLineEdit()
        self.name.setPlaceholderText("اسم الموظف")
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("رقم الهاتف (اختياري)")
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(70)
        self.notes.setPlaceholderText("ملاحظات...")

        form.addRow("الاسم *:", self.name)
        form.addRow("الهاتف:", self.phone)
        form.addRow("ملاحظات:", self.notes)
        lay.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        save_lbl = "حفظ التعديلات" if self.registrar else "حفظ"
        btns.button(QDialogButtonBox.StandardButton.Save).setText(save_lbl)
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        style_dialog_buttons(btns)
        lay.addWidget(btns)

    def _fill(self, r):
        self.name.setText(r["name"])
        self.phone.setText(r["phone"] or "")
        self.notes.setPlainText(r["notes"] or "")

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال اسم الموظف")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name.text().strip(),
            "phone": self.phone.text().strip(),
            "notes": self.notes.toPlainText().strip(),
        }


class RegistrarsWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.registrar_ids = []
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 25, 30, 25)
        root.setSpacing(15)

        hdr = QHBoxLayout()
        title = QLabel("المسجّلون")
        title.setObjectName("page_title")
        hdr.addWidget(title)
        hdr.addStretch()
        add_btn = QPushButton("➕ إضافة مسجّل")
        apply_button_style(add_btn, "primary")
        add_btn.clicked.connect(self.add_registrar)
        hdr.addWidget(add_btn)
        root.addLayout(hdr)

        hint = QLabel("الموظفون الذين يسجّلون عمليات الحجز على البرنامج")
        hint.setObjectName("page_subtitle")
        root.addWidget(hint)

        self.search = QLineEdit()
        self.search.setObjectName("search_bar")
        self.search.setPlaceholderText("🔍 بحث بالاسم أو الهاتف...")
        self.search.setFixedWidth(300)
        self.search.textChanged.connect(self.load_data)
        root.addWidget(self.search)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "رقم", "الاسم", "الهاتف", "حجوزات نشطة", "إجمالي الحجوزات"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.edit_registrar)
        root.addWidget(self.table)

        actions = QHBoxLayout()
        edit_btn = QPushButton("✏️ تعديل")
        apply_button_style(edit_btn, "secondary")
        edit_btn.clicked.connect(self.edit_registrar)
        archive_btn = QPushButton("🗑️ حذف")
        apply_button_style(archive_btn, "warning")
        archive_btn.clicked.connect(self.archive_registrar)
        actions.addWidget(edit_btn)
        actions.addWidget(archive_btn)
        actions.addStretch()
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color:#6B7280; font-size:12px;")
        actions.addWidget(self.count_lbl)
        root.addLayout(actions)

    def load_data(self):
        search = self.search.text().strip() or None
        rows = self.db.get_registrar_stats()
        if search:
            s = search.lower()
            rows = [
                r for r in rows
                if s in (r["name"] or "").lower() or s in (r["phone"] or "").lower()
            ]

        self.table.setRowCount(0)
        self.registrar_ids = []
        for r in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.registrar_ids.append(r["id"])
            vals = [
                str(r["id"]),
                r["name"],
                r["phone"] or "—",
                str(r["active_bookings"] or 0),
                str(r["bookings_count"] or 0),
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 3 and int(r["active_bookings"] or 0) > 0:
                    item.setForeground(QColor("#B45309"))
                self.table.setItem(i, col, item)
        self.count_lbl.setText(f"إجمالي: {len(rows)} مسجّل")

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.registrar_ids):
            QMessageBox.information(self, "تنبيه", "يرجى اختيار مسجّل أولاً")
            return None
        return self.registrar_ids[row]

    def add_registrar(self):
        dlg = RegistrarDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            rid = self.db.add_registrar(**data)
            self.load_data()
            row = next((i for i, x in enumerate(self.registrar_ids) if x == rid), -1)
            after_save(self, self.table, row, f"تم إضافة المسجّل «{data['name']}» بنجاح.")

    def edit_registrar(self):
        rid = self._selected_id()
        if not rid:
            return
        registrar = self.db.get_registrar(rid)
        dlg = RegistrarDialog(self, registrar)
        if dlg.exec():
            data = dlg.get_data()
            self.db.update_registrar(rid, **data)
            self.load_data()
            row = next((i for i, x in enumerate(self.registrar_ids) if x == rid), -1)
            after_save(self, self.table, row, f"تم تحديث بيانات المسجّل «{data['name']}» بنجاح.")

    def archive_registrar(self):
        rid = self._selected_id()
        if not rid:
            return
        registrar = self.db.get_registrar(rid)
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل تريد حذف المسجّل «{registrar['name']}»؟\nلن يظهر في قائمة الحجز الجديد.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if not AdminAuthDialog(self, self.db).exec():
                return
            ok, err = self.db.archive_registrar(rid)
            if not ok:
                QMessageBox.warning(self, "تعذر الحذف", err or "لا يمكن حذف المسجّل")
                return
            self.load_data()
            notify_success(self, f"تم حذف المسجّل «{registrar['name']}» بنجاح.")
