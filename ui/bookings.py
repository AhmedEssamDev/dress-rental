from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
                             QComboBox, QDialog, QFormLayout, QDoubleSpinBox, QTextEdit,
                             QMessageBox, QDialogButtonBox, QDateEdit, QListWidget, QInputDialog)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QPixmap
from styles import STATUS_AR, STATUS_COLOR, apply_button_style, style_dialog_buttons
from image_utils import resolve_image_path
from ui.image_viewer import ImageViewerDialog
from ui.feedback import after_save
from ui.admin_auth import AdminAuthDialog


class BookingDialog(QDialog):
    def __init__(self, parent, db, booking=None):
        super().__init__(parent)
        self.db = db
        self.booking = booking
        self.setWindowTitle("حجز فستان" if not booking else "تعديل الحجز")
        self.setMinimumWidth(560)
        self.setMinimumHeight(620)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.selected_customer_id = None
        self.selected_dress_id = None
        self._build()
        if booking:
            self._fill_data()
        else:
            self._search_customers("")
            self._search_dresses("")

    def _build(self):
        root_lay = QVBoxLayout(self)
        root_lay.setSpacing(15)

        cols_lay = QHBoxLayout()
        cols_lay.setSpacing(20)

        # --- Right Column (Customer & Details) ---
        right_col = QVBoxLayout()
        right_form = QFormLayout()
        right_form.setSpacing(10)

        self.cust_search = QLineEdit()
        self.cust_search.setPlaceholderText("بحث عميل بالاسم أو الهاتف...")
        self.cust_search.textChanged.connect(self._search_customers)
        self.cust_list = QListWidget()
        self.cust_list.setFixedHeight(120)
        self.cust_list.itemClicked.connect(self._select_customer)
        self.cust_lbl = QLabel("لم يتم اختيار عميل")
        self.cust_lbl.setStyleSheet("color:#6B7280; font-style:italic;")

        right_form.addRow("بحث عميل:", self.cust_search)
        right_form.addRow("", self.cust_list)
        right_form.addRow("العميل:", self.cust_lbl)

        self.registrar_combo = QComboBox()
        self._load_registrars()
        right_form.addRow("المسجّل *:", self.registrar_combo)

        self.reservation_date = QDateEdit(QDate.currentDate())
        self.reservation_date.setCalendarPopup(True)
        self.reservation_date.setDisplayFormat("yyyy-MM-dd")
        self.event_date = QDateEdit(QDate.currentDate().addDays(7))
        self.event_date.setCalendarPopup(True)
        self.event_date.setDisplayFormat("yyyy-MM-dd")
        self.expected_return_date = QDateEdit(QDate.currentDate().addDays(10))
        self.expected_return_date.setCalendarPopup(True)
        self.expected_return_date.setDisplayFormat("yyyy-MM-dd")

        right_form.addRow("تاريخ الحجز:", self.reservation_date)
        right_form.addRow("تاريخ المناسبة:", self.event_date)
        right_form.addRow("تاريخ الإرجاع:", self.expected_return_date)

        self.rental_price = QDoubleSpinBox()
        self.rental_price.setRange(0, 999999)
        self.rental_price.setDecimals(0)
        self.rental_price.setSuffix(" جنيه")
        self.deposit = QDoubleSpinBox()
        self.deposit.setRange(0, 999999)
        self.deposit.setDecimals(0)
        self.deposit.setSuffix(" جنيه")

        right_form.addRow("الإيجار:", self.rental_price)
        right_form.addRow("التأمين:", self.deposit)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText("ملاحظات الحجز...")
        right_form.addRow("ملاحظات:", self.notes)

        right_col.addLayout(right_form)
        right_col.addStretch()

        # --- Left Column (Dress Selection & Preview) ---
        left_col = QVBoxLayout()
        left_col.setSpacing(10)

        left_form = QFormLayout()
        left_form.setSpacing(10)
        
        self.dress_search = QLineEdit()
        self.dress_search.setPlaceholderText("بحث فستان بالاسم أو الكود...")
        self.dress_search.textChanged.connect(self._search_dresses)
        self.dress_list = QListWidget()
        self.dress_list.setFixedHeight(120)
        self.dress_list.itemClicked.connect(self._select_dress)
        self.dress_lbl = QLabel("لم يتم اختيار فستان")
        self.dress_lbl.setStyleSheet("color:#6B7280; font-style:italic;")

        left_form.addRow("بحث فستان:", self.dress_search)
        left_form.addRow("", self.dress_list)
        left_form.addRow("الفستان:", self.dress_lbl)

        left_col.addLayout(left_form)

        self.dress_preview = QLabel("لا توجد صورة")
        self.dress_preview.setFixedSize(220, 280)
        self.dress_preview.setStyleSheet("border: 1px solid #D1D5DB; background: #F3F4F6; border-radius: 4px;")
        self.dress_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dress_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dress_preview.mousePressEvent = self._on_preview_clicked

        img_lay = QHBoxLayout()
        img_lay.addStretch()
        img_lay.addWidget(self.dress_preview)
        img_lay.addStretch()
        
        left_col.addLayout(img_lay)
        left_col.addStretch()

        # --- Combine columns ---
        cols_lay.addLayout(right_col, stretch=1)
        cols_lay.addLayout(left_col, stretch=1)
        root_lay.addLayout(cols_lay)

        # --- Buttons ---
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("حفظ الحجز" if not self.booking else "حفظ التعديلات")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        style_dialog_buttons(btns)
        root_lay.addWidget(btns)

    def _fill_data(self):
        c = self.db.get_customer(self.booking["customer_id"])
        if c:
            self._customers = [c]
            self.cust_list.clear()
            self.cust_list.addItem(f"{c['name']} — {c['phone'] or '—'}")
            self.cust_list.setCurrentRow(0)
            self._select_customer()

        d = self.db.get_dress(self.booking["dress_id"])
        if d:
            self._dresses = [d]
            self.dress_list.clear()
            self.dress_list.addItem(f"{d['code']} — {d['name']} ({d['size'] or '—'})")
            self.dress_list.setCurrentRow(0)
            self._select_dress()

        idx = self.registrar_combo.findData(self.booking.get("registered_by_id"))
        if idx >= 0:
            self.registrar_combo.setCurrentIndex(idx)

        try:
            self.reservation_date.setDate(QDate.fromString(self.booking["reservation_date"], "yyyy-MM-dd"))
            self.event_date.setDate(QDate.fromString(self.booking["event_date"], "yyyy-MM-dd"))
            if self.booking.get("expected_return_date"):
                self.expected_return_date.setDate(QDate.fromString(self.booking["expected_return_date"], "yyyy-MM-dd"))
        except:
            pass

        self.rental_price.setValue(self.booking.get("rental_price", 0))
        self.deposit.setValue(self.booking.get("deposit", 0))
        self.notes.setPlainText(self.booking.get("notes", ""))

    def _load_registrars(self):
        self.registrar_combo.clear()
        rows = self.db.get_all_registrars()
        for r in rows:
            self.registrar_combo.addItem(r["name"], r["id"])
        if not rows:
            self.registrar_combo.addItem("— لا يوجد مسجّلون —", None)

    def _search_customers(self, text):
        self._customers = self.db.get_all_customers(search=text if text else None)
        self.cust_list.clear()
        for c in self._customers:
            self.cust_list.addItem(f"{c['name']} — {c['phone'] or '—'}")

    def _search_dresses(self, text):
        dresses = self.db.get_available_dresses()
        if text:
            s = text.lower()
            dresses = [d for d in dresses if s in d["name"].lower() or s in d["code"].lower()]
        self._dresses = dresses
        self.dress_list.clear()
        for d in self._dresses:
            self.dress_list.addItem(f"{d['code']} — {d['name']} ({d['size'] or '—'})")

    def _select_customer(self, *_):
        idx = self.cust_list.currentRow()
        if idx < 0 or idx >= len(self._customers):
            return
        c = self._customers[idx]
        self.selected_customer_id = c["id"]
        self.cust_lbl.setText(f"✅ {c['name']} ({c['phone'] or '—'})")
        self.cust_lbl.setStyleSheet("color:#065F46; font-weight:bold;")

    def _select_dress(self, *_):
        idx = self.dress_list.currentRow()
        if idx < 0 or idx >= len(self._dresses):
            return
        d = self._dresses[idx]
        self.selected_dress_id = d["id"]
        self.rental_price.setValue(d["rental_price"])
        self.deposit.setValue(d["deposit"] or 0)
        self.dress_lbl.setText(f"✅ {d['name']} — كود: {d['code']}")
        self.dress_lbl.setStyleSheet("color:#065F46; font-weight:bold;")

        full = resolve_image_path(dict(d).get("image_path"))
        if full:
            pix = QPixmap(full)
            if not pix.isNull():
                self.dress_preview.setText("")
                self.dress_preview.setPixmap(pix.scaled(220, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.dress_preview.setText("لا توجد صورة")
        else:
            self.dress_preview.setText("لا توجد صورة")

    def _on_preview_clicked(self, event):
        if not self.selected_dress_id:
            return
        idx = self.dress_list.currentRow()
        if idx >= 0:
            d = self._dresses[idx]
            full = resolve_image_path(dict(d).get("image_path"))
            if full:
                ImageViewerDialog(self, full, f"صورة الفستان: {d['name']}").exec()

    def _save(self):
        if not self.selected_customer_id:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار عميل")
            return
        if not self.selected_dress_id:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار فستان")
            return
        if self.rental_price.value() <= 0:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال سعر إيجار صحيح")
            return
        if self.event_date.date() < self.reservation_date.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ المناسبة يجب أن يكون بعد تاريخ الحجز")
            return
        registrar_id = self.registrar_combo.currentData()
        if not registrar_id:
            QMessageBox.warning(
                self, "تنبيه",
                "يرجى اختيار الموظف المسجّل للحجز.\nيمكنك إضافة موظفين من صفحة «المسجّلون».",
            )
            return
        self.accept()

    def get_data(self):
        return {
            "dress_id": self.selected_dress_id,
            "customer_id": self.selected_customer_id,
            "registered_by_id": self.registrar_combo.currentData(),
            "reservation_date": self.reservation_date.date().toString("yyyy-MM-dd"),
            "event_date": self.event_date.date().toString("yyyy-MM-dd"),
            "expected_return_date": self.expected_return_date.date().toString("yyyy-MM-dd"),
            "rental_price": self.rental_price.value(),
            "deposit": self.deposit.value(),
            "notes": self.notes.toPlainText().strip(),
        }


class BookingsWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.booking_ids = []
        self.current_page = 1
        self.items_per_page = 50
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 25, 30, 25)
        root.setSpacing(15)

        hdr = QHBoxLayout()
        title = QLabel("إدارة الحجوزات")
        title.setObjectName("page_title")
        hdr.addWidget(title)
        hdr.addStretch()
        add_btn = QPushButton("➕ حجز جديد")
        apply_button_style(add_btn, "primary")
        add_btn.clicked.connect(self.add_booking)
        hdr.addWidget(add_btn)
        root.addLayout(hdr)

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setObjectName("search_bar")
        self.search.setPlaceholderText("🔍 بحث بالعميل أو الفستان أو المسجّل...")
        self.search.setFixedWidth(300)
        self.search.textChanged.connect(self.load_data)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["الكل", "نشط", "ملغي", "تم التحويل"])
        self.status_filter.currentIndexChanged.connect(self.load_data)
        self.status_filter.setFixedWidth(150)
        filters.addWidget(self.search)
        filters.addWidget(QLabel("الحالة:"))
        filters.addWidget(self.status_filter)
        filters.addStretch()
        root.addLayout(filters)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "رقم", "العميل", "المسجّل", "الفستان", "الصورة", "تاريخ الحجز", "تاريخ المناسبة",
            "سعر الإيجار", "التأمين", "الحالة"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self._on_cell_double_click)
        root.addWidget(self.table)

        actions = QHBoxLayout()
        edit_btn = QPushButton("✏️ تعديل الحجز")
        apply_button_style(edit_btn, "primary")
        edit_btn.clicked.connect(self.edit_booking)
        
        convert_btn = QPushButton("📦 تحويل لتأجير")
        apply_button_style(convert_btn, "success")
        convert_btn.clicked.connect(self.convert_booking)
        
        cancel_btn = QPushButton("❌ إلغاء الحجز")
        apply_button_style(cancel_btn, "secondary")
        cancel_btn.clicked.connect(self.cancel_booking)
        
        delete_btn = QPushButton("🗑️ حذف نهائي")
        apply_button_style(delete_btn, "danger")
        delete_btn.clicked.connect(self.delete_booking)
        
        actions.addWidget(edit_btn)
        actions.addWidget(convert_btn)
        actions.addWidget(cancel_btn)
        actions.addWidget(delete_btn)
        actions.addStretch()
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color:#6B7280; font-size:12px;")
        actions.addWidget(self.count_lbl)
        root.addLayout(actions)

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

    @staticmethod
    def _image_cell(relative_path, width=72, height=72):
        lbl = QLabel("—")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        full = resolve_image_path(relative_path)
        if not full:
            return lbl
        pix = QPixmap(full)
        if pix.isNull():
            return lbl
        lbl.setText("")
        lbl.setPixmap(
            pix.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )
        return lbl

    def focus_booking(self, booking_id):
        for row, bid in enumerate(self.booking_ids):
            if bid == booking_id:
                self.table.selectRow(row)
                self.table.scrollToItem(self.table.item(row, 0))
                break

    def load_data(self):
        status_map = {0: None, 1: "active", 2: "cancelled", 3: "converted"}
        status = status_map.get(self.status_filter.currentIndex())
        search = self.search.text().strip() or None
        
        offset = (self.current_page - 1) * self.items_per_page
        rows = self.db.get_all_bookings(status=status, search=search, limit=self.items_per_page, offset=offset)
        total_count = self.db.get_bookings_count(status=status, search=search)
        self.table.setRowCount(0)
        self.booking_ids = []
        for b in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.table.setRowHeight(i, 82)
            self.booking_ids.append(b["id"])
            vals = [
                str(b["id"]),
                b["customer_name"],
                b["registrar_name"] or "—",
                b["dress_name"],
                b["reservation_date"],
                b["event_date"],
                f"{b['rental_price']:,.0f} ج",
                f"{b['deposit'] or 0:,.0f} ج",
            ]
            for col, val in enumerate(vals):
                if col >= 4:
                    table_col = col + 1
                else:
                    table_col = col
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, table_col, item)
            self.table.setCellWidget(i, 4, self._image_cell(b["image_path"]))
            st = b["status"]
            status_item = QTableWidgetItem(STATUS_AR.get(st, st))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            color = STATUS_COLOR.get(st, "#6B7280")
            status_item.setForeground(QColor(color))
            status_item.setBackground(QColor(color + "22"))
            self.table.setItem(i, 9, status_item)
            
        total_pages = (total_count + self.items_per_page - 1) // self.items_per_page
        if total_pages == 0: total_pages = 1
        self.page_lbl.setText(f"صفحة {self.current_page} من {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)
        self.count_lbl.setText(f"إجمالي: {total_count} حجز")

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def next_page(self):
        self.current_page += 1
        self.load_data()

    def _on_cell_double_click(self, row, col):
        if row < 0 or row >= len(self.booking_ids):
            return
        booking = self.db.get_booking(self.booking_ids[row])
        if col == 4:
            full = resolve_image_path(booking["image_path"] if booking else None)
            if not full:
                QMessageBox.information(self, "تنبيه", "لا توجد صورة لهذا الفستان")
                return
            ImageViewerDialog(self, full, f"صورة الفستان: {booking['dress_name']}").exec()
        else:
            self.table.selectRow(row)
            if booking["status"] == "active":
                self.edit_booking()
            else:
                QMessageBox.information(
                    self, "تفاصيل الحجز",
                    f"العميل: {booking['customer_name']}\nالفستان: {booking['dress_name']}\n"
                    f"تاريخ المناسبة: {booking['event_date']}\nالحالة: {STATUS_AR.get(booking['status'], booking['status'])}"
                )

    def _selected_booking(self):
        row = self.table.currentRow()
        if row < 0 and self.table.selectedItems():
            row = self.table.selectedItems()[0].row()
        if row < 0 or row >= len(self.booking_ids):
            QMessageBox.information(self, "تنبيه", "يرجى اختيار حجز أولاً")
            return None
        return self.db.get_booking(self.booking_ids[row])

    def edit_booking(self):
        booking = self._selected_booking()
        if not booking:
            QMessageBox.warning(self, "تنبيه", "يرجى تحديد حجز أولاً")
            return
            
        if self.db._normalize_booking_status(booking["status"]) != "active":
            QMessageBox.warning(self, "تنبيه", "لا يمكن تعديل إلا الحجوزات النشطة.")
            return

        dlg = BookingDialog(self, self.db, booking=booking)
        if dlg.exec():
            data = dlg.get_data()
            success = self.db.update_booking(
                bid=booking["id"],
                dress_id=data["dress_id"],
                customer_id=data["customer_id"],
                reservation_date=data["reservation_date"],
                event_date=data["event_date"],
                expected_return_date=data["expected_return_date"],
                rental_price=data["rental_price"],
                deposit=data["deposit"],
                notes=data["notes"],
                registered_by_id=data["registered_by_id"]
            )
            if not success:
                QMessageBox.warning(self, "تنبيه", "هذا الفستان محجوز بالفعل في فترة زمنية متداخلة")
                return
            
            self.load_data()
            row = next((i for i, x in enumerate(self.booking_ids) if x == booking["id"]), -1)
            after_save(self, self.table, row, f"تم تعديل الحجز بنجاح.\nرقم الحجز: {booking['id']}")

    def add_booking(self):
        if not self.db.get_all_registrars():
            QMessageBox.warning(
                self, "تنبيه",
                "لا يوجد مسجّلون في النظام.\nيرجى إضافة موظف واحد على الأقل من صفحة «المسجّلون» قبل إنشاء حجز.",
            )
            return
        dlg = BookingDialog(self, self.db)
        if dlg.exec():
            bid = self.db.add_booking(**dlg.get_data())
            if bid is None:
                QMessageBox.warning(self, "تنبيه", "هذا الفستان محجوز بالفعل في فترة زمنية متداخلة")
                return
            self.load_data()
            row = next((i for i, x in enumerate(self.booking_ids) if x == bid), -1)
            after_save(self, self.table, row, f"تم حفظ الحجز بنجاح.\nرقم الحجز: {bid}")
            
            from ui.owner_notify import notify_owner_action
            booking_record = self.db.get_booking(bid)
            if booking_record:
                notify_owner_action(self.db, "حجز جديد", dict(booking_record))

    def cancel_booking(self):
        booking = self._selected_booking()
        if not booking:
            return
        reply = QMessageBox.question(
            self, "تأكيد الإلغاء", "هل تريد إلغاء هذا الحجز؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok, err = self.db.cancel_booking(booking["id"])
            if not ok:
                QMessageBox.warning(self, "تعذر الإلغاء", err or "تعذر إلغاء الحجز")
                return
            self.load_data()
            QMessageBox.information(self, "نجاح ✅", "تم إلغاء الحجز بنجاح")

    def delete_booking(self):
        booking = self._selected_booking()
        if not booking:
            return
        reply = QMessageBox.question(
            self, "تأكيد الحذف", "هل أنت متأكد أنك تريد حذف هذا الحجز نهائياً من النظام؟\nهذا الإجراء لا يمكن التراجع عنه.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if not AdminAuthDialog(self, self.db).exec():
                return
            ok, err = self.db.delete_booking(booking["id"])
            if not ok:
                QMessageBox.warning(self, "تعذر الحذف", err or "تعذر حذف الحجز")
                return
            self.load_data()
            QMessageBox.information(self, "نجاح ✅", "تم حذف الحجز نهائياً بنجاح")

    def convert_booking(self):
        booking = self._selected_booking()
        if not booking:
            return
        if booking["status"] != "active":
            QMessageBox.warning(self, "تنبيه", "هذا الحجز غير نشط")
            return
        paid, ok = QInputDialog.getDouble(
            self, "تحويل لتأجير", "المدفوع عند التحويل:", min=0, max=999999, decimals=0
        )
        if not ok:
            return
        rid = self.db.convert_booking_to_rental(booking["id"], paid_amount=paid)
        if rid:
            self.load_data()
            QMessageBox.information(self, "نجاح ✅", f"تم التحويل إلى تأجير رقم: {rid}")
        else:
            QMessageBox.warning(self, "تنبيه", "لا يمكن تحويل الحجز حالياً (قد يكون الفستان غير متاح)")
