from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
                             QComboBox, QDialog, QFormLayout, QDoubleSpinBox, QTextEdit,
                             QMessageBox, QDialogButtonBox, QDateEdit, QGroupBox,
                             QFrame, QSplitter, QListWidget, QListWidgetItem, QSpinBox,
                             QScrollArea, QGridLayout, QSizePolicy, QTabWidget)
from PyQt6.QtCore import Qt, QDate, QSize
from PyQt6.QtGui import QColor, QFont, QPixmap, QIcon
from image_utils import resolve_image_path
from styles import (STATUS_AR, STATUS_COLOR, style_dialog_buttons, apply_button_style,
                    make_form_label, style_form_input, setup_form_layout, RENTAL_DIALOG_STYLE,
                    section_title_label, make_rental_section_frame, make_selection_chip,
                    set_selection_chip, LIST_STYLE)
from datetime import date
from ui.image_viewer import ImageViewerDialog
from ui.feedback import after_save, notify_success, focus_table_row
from ui.admin_auth import AdminAuthDialog


class NewRentalDialog(QDialog):
    def __init__(self, parent, db, rental=None):
        super().__init__(parent)
        self.db = db
        self.rental = rental
        self.setObjectName("new_rental_dialog")
        self.setWindowTitle("تأجير فستان جديد" if not rental else f"تعديل تأجير رقم {rental['id']}")
        self.setMinimumSize(900, 480)
        self.resize(950, 520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(RENTAL_DIALOG_STYLE)
        self._build()
        self._search_customers("")
        self._search_dresses("")
        if rental:
            self._fill(rental)
            self.h_title.setText("تعديل بيانات التأجير")
            self.save_btn.setText("💾 حفظ التعديلات")
        self._recalc()

    def _fill(self, r):
        # تعبئة العميل
        self.selected_customer_id = r['customer_id']
        set_selection_chip(self.cust_label, f"✅  {r['customer_name']}  —  {r['customer_phone'] or 'بدون هاتف'}")
        
        # تعبئة الفستان
        self.selected_dress_id = r['dress_id']
        img_note = "  |  📷 صورة متوفرة" if r['image_path'] else "  |  ⚠️ بدون صورة"
        set_selection_chip(
            self.dress_label,
            f"✅  {r['dress_name']}  |  كود: {r['dress_code']}  |  مقاس: {r['size'] or '—'}  |  {r['rental_price']:,.0f} ج{img_note}"
        )
        self._show_dress_preview(r)
        
        # تعبئة المبالغ والتواريخ
        self.rental_date.setDate(QDate.fromString(r['rental_date'], "yyyy-MM-dd"))
        self.return_date.setDate(QDate.fromString(r['expected_return_date'], "yyyy-MM-dd"))
        self.price.setValue(r['rental_price'])
        self.deposit.setValue(r['deposit'] or 0)
        self.discount.setValue(r['discount'] or 0)
        self.paid.setValue(r['paid_amount'] or 0)
        self.notes.setPlainText(r['notes'] or '')

    def _step_badge(self, num, color):
        badge = QLabel(str(num))
        badge.setFixedSize(24, 24)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background:{color}; color:#FFFFFF; font-size:12px; font-weight:bold;"
            "border-radius:12px;"
        )
        return badge

    @staticmethod
    def _dress_image_path(dress):
        path = dress["image_path"] if dress["image_path"] else None
        return path

    def _dress_thumbnail(self, dress, width=48, height=48):
        full = resolve_image_path(self._dress_image_path(dress))
        if not full:
            return None
        pix = QPixmap(full)
        if pix.isNull():
            return None
        return pix.scaled(
            width, height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _show_dress_preview(self, dress=None):
        if dress and self._dress_image_path(dress):
            full = resolve_image_path(self._dress_image_path(dress))
            if full:
                pix = QPixmap(full)
                if not pix.isNull():
                    self.dress_preview.setText("")
                    self.dress_preview.setPixmap(pix.scaled(
                        120, 160,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    ))
                    return
        self.dress_preview.setPixmap(QPixmap())
        self.dress_preview.setText("👗")

    def _field_block(self, title, widget):
        block = QVBoxLayout()
        block.setSpacing(4)
        lbl = QLabel(title)
        lbl.setStyleSheet("color:#475569; font-size:12px; font-weight:bold; background:transparent;")
        block.addWidget(lbl)
        block.addWidget(widget)
        wrap = QWidget()
        wrap.setLayout(block)
        return wrap

    def _build_section_header(self, step, title, subtitle, color):
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self._step_badge(step, color))
        row.addWidget(section_title_label(title, subtitle), stretch=1)
        return row

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── شريط العنوان ──
        header = QFrame()
        header.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            " stop:0 #3A2A32, stop:1 #7D5A6A);"
        )
        header_lay = QVBoxLayout(header)
        header_lay.setContentsMargins(20, 10, 20, 10)
        self.h_title = QLabel("تأجير فستان جديد")
        self.h_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.h_title.setStyleSheet("color:#FFFFFF; background:transparent;")
        header_lay.addWidget(self.h_title)
        root.addWidget(header)

        # ── المحتوى الرئيسي ──
        main_content = QWidget()
        main_lay = QHBoxLayout(main_content)
        main_lay.setContentsMargins(15, 15, 15, 15)
        main_lay.setSpacing(15)

        # ── الجانب الأيمن: التبويبات (الاختيار) ──
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #CBD5E1; border-radius: 8px; background: white; }
            QTabBar::tab { background: #F1F5F9; padding: 8px 20px; font-weight: bold; color: #64748B; border-radius: 6px 6px 0 0; }
            QTabBar::tab:selected { background: white; color: #7D5A6A; border-bottom: 2px solid #C9A86C; }
        """)

        # تبويب 1: العميل
        cust_tab = QWidget()
        cust_lay = QVBoxLayout(cust_tab)
        cust_lay.setContentsMargins(15, 15, 15, 15)
        cust_lay.setSpacing(10)
        
        cust_search_row = QHBoxLayout()
        self.cust_search = QLineEdit()
        self.cust_search.setPlaceholderText("🔍 ابحث بالاسم أو الهاتف...")
        style_form_input(self.cust_search, min_height=34)
        self.cust_search.textChanged.connect(self._search_customers)
        cust_search_row.addWidget(self.cust_search)
        
        new_cust_btn = QPushButton("+")
        apply_button_style(new_cust_btn, "primary")
        new_cust_btn.setFixedSize(34, 34)
        new_cust_btn.clicked.connect(self._add_new_customer)
        cust_search_row.addWidget(new_cust_btn)
        cust_lay.addLayout(cust_search_row)

        self.cust_list = QListWidget()
        self.cust_list.setStyleSheet(LIST_STYLE)
        self.cust_list.itemClicked.connect(self._select_customer)
        cust_lay.addWidget(self.cust_list)

        self.cust_label = make_selection_chip()
        self.cust_label.setMinimumHeight(38)
        cust_lay.addWidget(self.cust_label)
        
        self.tabs.addTab(cust_tab, "👥 اختيار العميل")

        # تبويب 2: الفستان
        dress_tab = QWidget()
        dress_lay = QVBoxLayout(dress_tab)
        dress_lay.setContentsMargins(15, 15, 15, 15)
        dress_lay.setSpacing(10)

        self.dress_search = QLineEdit()
        self.dress_search.setPlaceholderText("🔍 ابحث بالكود أو الاسم...")
        style_form_input(self.dress_search, min_height=34)
        self.dress_search.textChanged.connect(self._search_dresses)
        dress_lay.addWidget(self.dress_search)

        dress_row = QHBoxLayout()
        self.dress_list = QListWidget()
        self.dress_list.setIconSize(QSize(40, 40))
        self.dress_list.setStyleSheet(LIST_STYLE)
        self.dress_list.itemClicked.connect(self._select_dress)
        self.dress_list.currentRowChanged.connect(self._preview_dress_row)
        dress_row.addWidget(self.dress_list, stretch=1)

        self.dress_preview = QLabel()
        self.dress_preview.setFixedSize(120, 160)
        self.dress_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dress_preview.setStyleSheet("background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px;")
        self.dress_preview.setText("👗")
        dress_row.addWidget(self.dress_preview)
        dress_lay.addLayout(dress_row)

        self.dress_label = make_selection_chip()
        self.dress_label.setMinimumHeight(38)
        dress_lay.addWidget(self.dress_label)
        
        self.tabs.addTab(dress_tab, "👗 اختيار الفستان")
        
        main_lay.addWidget(self.tabs, stretch=3)

        # ── الجانب الأيسر: التفاصيل (ثابت) ──
        det_card = make_rental_section_frame("#059669")
        det_lay = QVBoxLayout(det_card)
        det_lay.setContentsMargins(15, 12, 15, 12)
        det_lay.setSpacing(8)
        det_lay.addLayout(self._build_section_header(3, "التفاصيل", "الدفع والتواريخ", "#059669"))

        dates_row = QHBoxLayout()
        self.rental_date = QDateEdit(QDate.currentDate()); self.rental_date.setCalendarPopup(True)
        style_form_input(self.rental_date, min_height=34)
        self.return_date = QDateEdit(QDate.currentDate().addDays(3)); self.return_date.setCalendarPopup(True)
        style_form_input(self.return_date, min_height=34)
        dates_row.addWidget(self._field_block("📅 الاستلام", self.rental_date))
        dates_row.addWidget(self._field_block("📅 الإرجاع", self.return_date))
        det_lay.addLayout(dates_row)

        money_grid = QGridLayout()
        money_grid.setSpacing(8)
        self.price = QDoubleSpinBox(); self.price.setRange(0, 999999); self.price.setDecimals(0); self.price.setSuffix(" ج")
        style_form_input(self.price, min_height=34); self.price.valueChanged.connect(self._recalc)
        self.deposit = QDoubleSpinBox(); self.deposit.setRange(0, 999999); self.deposit.setDecimals(0); self.deposit.setSuffix(" ج")
        style_form_input(self.deposit, min_height=34)
        self.discount = QDoubleSpinBox(); self.discount.setRange(0, 999999); self.discount.setDecimals(0); self.discount.setSuffix(" ج")
        style_form_input(self.discount, min_height=34); self.discount.valueChanged.connect(self._recalc)
        self.paid = QDoubleSpinBox(); self.paid.setRange(0, 999999); self.paid.setDecimals(0); self.paid.setSuffix(" ج")
        style_form_input(self.paid, min_height=34); self.paid.valueChanged.connect(self._recalc)

        money_grid.addWidget(self._field_block("💰 السعر", self.price), 0, 0)
        money_grid.addWidget(self._field_block("🔒 التأمين", self.deposit), 0, 1)
        money_grid.addWidget(self._field_block("🏷️ الخصم", self.discount), 1, 0)
        money_grid.addWidget(self._field_block("💵 المدفوع", self.paid), 1, 1)
        det_lay.addLayout(money_grid)

        summary = QFrame()
        summary.setStyleSheet("background:#F1F5F9; border-radius:8px;")
        sum_lay = QHBoxLayout(summary)
        sum_lay.setContentsMargins(10, 5, 10, 5)
        self.total_lbl = QLabel("0"); self.total_lbl.setStyleSheet("font-size:16px; font-weight:bold; color:#1E40AF;")
        self.remaining_lbl = QLabel("0"); self.remaining_lbl.setStyleSheet("font-size:16px; font-weight:bold; color:#B91C1C;")
        
        def _sum_item(cap, lbl, clr):
            v = QVBoxLayout(); v.setSpacing(0)
            c = QLabel(cap); c.setStyleSheet(f"color:{clr}; font-size:10px; font-weight:bold;")
            c.setAlignment(Qt.AlignmentFlag.AlignCenter); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(c); v.addWidget(lbl)
            return v

        sum_lay.addLayout(_sum_item("الإجمالي", self.total_lbl, "#1E40AF"))
        sum_lay.addLayout(_sum_item("المتبقي", self.remaining_lbl, "#B91C1C"))
        det_lay.addWidget(summary)

        self.notes = QTextEdit(); self.notes.setPlaceholderText("ملاحظات..."); self.notes.setMaximumHeight(50)
        style_form_input(self.notes, min_height=40)
        det_lay.addWidget(self._field_block("📝 ملاحظات", self.notes))
        
        main_lay.addWidget(det_card, stretch=2)
        root.addWidget(main_content)

        # ── الأزرار ──
        footer = QFrame()
        footer.setStyleSheet("background:#FFFFFF; border-top:1px solid #E2E8F0;")
        footer_lay = QHBoxLayout(footer)
        footer_lay.setContentsMargins(15, 8, 15, 8)

        cancel_btn = QPushButton("إلغاء"); apply_button_style(cancel_btn, "secondary")
        cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("✅ تأكيد"); apply_button_style(self.save_btn, "success")
        self.save_btn.setMinimumWidth(120)
        self.save_btn.clicked.connect(self._save)
        
        footer_lay.addWidget(cancel_btn)
        footer_lay.addStretch()
        footer_lay.addWidget(self.save_btn)
        root.addWidget(footer)

        self.selected_customer_id = None
        self.selected_dress_id = None

        self._search_customers("")
        self._search_dresses("")
        self._recalc()

    def _search_customers(self, text):
        customers = self.db.get_all_customers(search=text if text else None)
        self.cust_list.clear()
        self._customers = customers
        for c in customers:
            self.cust_list.addItem(f"{c['name']} — {c['phone'] or '—'}")

    def _search_dresses(self, text):
        dresses = self.db.get_available_dresses()
        
        # إذا كنا في وضع التعديل، يجب أن يظهر الفستان الحالي في القائمة
        if self.rental:
            curr = self.db.get_dress(self.rental['dress_id'])
            if curr and curr['id'] not in [d['id'] for d in dresses]:
                dresses.insert(0, curr)

        if text:
            text = text.lower()
            dresses = [d for d in dresses if text in d['name'].lower() or text in d['code'].lower()]
        self.dress_list.blockSignals(True)
        self.dress_list.clear()
        self.dress_list.blockSignals(False)
        self._dresses = dresses
        for d in dresses:
            label = f"{d['code']} — {d['name']}\nمقاس: {d['size'] or '—'}  |  {d['rental_price']:,.0f} ج"
            item = QListWidgetItem(label)
            thumb = self._dress_thumbnail(d, 64, 64)
            if thumb:
                item.setIcon(QIcon(thumb))
            else:
                item.setIcon(QIcon())
            self.dress_list.addItem(item)
        if dresses:
            self.dress_list.setCurrentRow(0)
            self._preview_dress_row(0)
        else:
            self._show_dress_preview(None)

    def _preview_dress_row(self, row):
        if row < 0 or row >= len(self._dresses):
            self._show_dress_preview(None)
            return
        self._show_dress_preview(self._dresses[row])

    def _select_customer(self, item):
        idx = self.cust_list.currentRow()
        if idx < 0 or idx >= len(self._customers):
            return
        c = self._customers[idx]
        self.selected_customer_id = c['id']
        set_selection_chip(self.cust_label, f"✅  {c['name']}  —  {c['phone'] or 'بدون هاتف'}")

    def _select_dress(self, item):
        idx = self.dress_list.currentRow()
        if idx < 0 or idx >= len(self._dresses):
            return
        d = self._dresses[idx]
        self.selected_dress_id = d['id']
        self._show_dress_preview(d)
        img_note = "  |  📷 صورة متوفرة" if self._dress_image_path(d) else "  |  ⚠️ بدون صورة"
        set_selection_chip(
            self.dress_label,
            f"✅  {d['name']}  |  كود: {d['code']}  |  مقاس: {d['size'] or '—'}  |  {d['rental_price']:,.0f} ج{img_note}"
        )
        self.price.setValue(d['rental_price'])
        self.deposit.setValue(d['deposit'] or 0)
        self._recalc()

    def _add_new_customer(self):
        from ui.customers import CustomerDialog
        dlg = CustomerDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            cid = self.db.add_customer(**data)
            self.selected_customer_id = cid
            set_selection_chip(
                self.cust_label, f"✅  {data['name']}  —  {data['phone'] or 'بدون هاتف'}"
            )
            self._search_customers("")

    def _recalc(self):
        total = max(0, self.price.value() - self.discount.value())
        remaining = max(0, total - self.paid.value())
        self.total_lbl.setText(f"{total:,.0f}")
        self.remaining_lbl.setText(f"{remaining:,.0f}")

    def _save(self):
        if not self.selected_customer_id:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار عميل"); return
        if not self.selected_dress_id:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار فستان"); return
        if self.rental_date.date() > self.return_date.date():
            QMessageBox.warning(self, "تنبيه", "موعد الإرجاع يجب أن يكون بعد تاريخ الاستلام"); return
        if self.price.value() <= 0:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال سعر الإيجار"); return
        self.accept()

    def get_data(self):
        total = max(0, self.price.value() - self.discount.value())
        return {
            'dress_id': self.selected_dress_id,
            'customer_id': self.selected_customer_id,
            'rental_date': self.rental_date.date().toString("yyyy-MM-dd"),
            'expected_return_date': self.return_date.date().toString("yyyy-MM-dd"),
            'rental_price': self.price.value(),
            'deposit': self.deposit.value(),
            'discount': self.discount.value(),
            'total_amount': total,
            'paid_amount': self.paid.value(),
            'notes': self.notes.toPlainText().strip(),
        }


class ReturnDialog(QDialog):
    def __init__(self, parent, db, rental):
        super().__init__(parent)
        self.db = db
        self.rental = rental
        self.setWindowTitle(f"إرجاع فستان — {rental['dress_name']}")
        self.setMinimumWidth(480)
        self.setMinimumHeight(520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(20)

        header = QLabel("↩️  إرجاع الفستان")
        header.setStyleSheet(
            "font-size:18px; font-weight:bold; color:#111827; padding-bottom:4px;"
        )
        lay.addWidget(header)

        info = QLabel(
            f"<b>العميل:</b> {self.rental['customer_name']}<br>"
            f"<b>الفستان:</b> {self.rental['dress_name']} ({self.rental['dress_code']})<br>"
            f"<b>المبلغ الإجمالي:</b> {self.rental['total_amount']:,.0f} جنيه<br>"
            f"<b>المدفوع:</b> {self.rental['paid_amount']:,.0f} جنيه<br>"
            f"<b>المتبقي:</b> {self.rental['remaining_amount']:,.0f} جنيه"
        )
        info.setWordWrap(True)
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setStyleSheet(
            "background:#F3F4F6; color:#111827; padding:18px; border-radius:10px; "
            "font-size:14px; line-height:1.8; border:1px solid #D1D5DB;"
        )
        lay.addWidget(info)

        details_group = QGroupBox("تفاصيل الإرجاع")
        form = QFormLayout(details_group)
        setup_form_layout(form)

        self.return_date = QDateEdit(QDate.currentDate())
        self.return_date.setCalendarPopup(True)
        self.return_date.setDisplayFormat("yyyy-MM-dd")
        style_form_input(self.return_date)

        self.additional = QDoubleSpinBox()
        self.additional.setRange(0, 999999)
        self.additional.setSuffix(" جنيه"); self.additional.setDecimals(0)
        self.additional.setValue(max(0, self.rental['remaining_amount']))
        style_form_input(self.additional)

        self.method = QComboBox()
        self.method.addItems(["كاش", "بطاقة", "تحويل"])
        style_form_input(self.method)

        form.addRow(make_form_label("تاريخ الإرجاع:"), self.return_date)
        form.addRow(make_form_label("مبلغ إضافي:"), self.additional)
        form.addRow(make_form_label("طريقة الدفع:"), self.method)
        lay.addWidget(details_group)

        lay.addSpacing(8)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("✅  تأكيد الإرجاع")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        style_dialog_buttons(btns)
        lay.addWidget(btns)

    def get_data(self):
        method_map = {0: 'cash', 1: 'card', 2: 'transfer'}
        return {
            'actual_return_date': self.return_date.date().toString("yyyy-MM-dd"),
            'additional_payment': self.additional.value(),
            'method': method_map.get(self.method.currentIndex(), 'cash'),
        }


class RentalsWidget(QWidget):
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
        title = QLabel("إدارة التأجيرات")
        title.setObjectName("page_title")
        hdr.addWidget(title)
        hdr.addStretch()
        add_btn = QPushButton("➕  تأجير فستان جديد")
        apply_button_style(add_btn, "primary")
        add_btn.clicked.connect(self.add_rental)
        hdr.addWidget(add_btn)
        root.addLayout(hdr)

        # Filters
        filters = QHBoxLayout(); filters.setSpacing(10)
        self.search = QLineEdit()
        self.search.setObjectName("search_bar")
        self.search.setPlaceholderText("🔍  بحث بالعميل أو الفستان...")
        self.search.setFixedWidth(280)
        self.search.textChanged.connect(self.load_data)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["الكل", "نشط", "متأخر", "مُرجع", "ملغي"])
        self.status_filter.currentIndexChanged.connect(self.load_data)
        self.status_filter.setFixedWidth(130)

        filters.addWidget(self.search)
        filters.addWidget(QLabel("الحالة:"))
        filters.addWidget(self.status_filter)
        filters.addStretch()
        root.addLayout(filters)

        # Table
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            ["رقم", "العميل", "الفستان", "الصورة", "تاريخ الاستلام",
             "موعد الإرجاع", "الإجمالي", "المدفوع", "المتبقي", "الحالة"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self._on_cell_double_click)
        root.addWidget(self.table)

        # Action buttons
        action = QHBoxLayout(); action.setSpacing(10)
        ret_btn = QPushButton("↩️  إرجاع الفستان")
        apply_button_style(ret_btn, "success")
        ret_btn.clicked.connect(self.return_dress)

        pay_btn = QPushButton("💵  إضافة دفعة")
        apply_button_style(pay_btn, "primary")
        pay_btn.clicked.connect(self.add_payment)

        edit_btn = QPushButton("✏️  تعديل")
        apply_button_style(edit_btn, "warning")
        edit_btn.clicked.connect(self.edit_rental)

        inv_btn = QPushButton("🧾  طباعة فاتورة")
        apply_button_style(inv_btn, "secondary")
        inv_btn.clicked.connect(self.print_invoice)

        cancel_btn = QPushButton("❌  إلغاء التأجير")
        apply_button_style(cancel_btn, "secondary") # Changed style so delete can be danger
        cancel_btn.clicked.connect(self.cancel_rental)

        delete_btn = QPushButton("🗑️  حذف نهائي")
        apply_button_style(delete_btn, "danger")
        delete_btn.clicked.connect(self.delete_rental)

        action.addWidget(ret_btn)
        action.addWidget(pay_btn)
        action.addWidget(edit_btn)
        action.addWidget(inv_btn)
        action.addWidget(cancel_btn)
        action.addWidget(delete_btn)
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

        self.rental_ids = []

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

    def load_data(self):
        self.db.update_overdue_status()
        status_map = {0: None, 1: 'active', 2: 'overdue', 3: 'returned', 4: 'cancelled'}
        status = status_map.get(self.status_filter.currentIndex())
        search = self.search.text().strip() or None
        
        offset = (self.current_page - 1) * self.items_per_page
        rows = self.db.get_all_rentals(status=status, search=search, limit=self.items_per_page, offset=offset)
        total_count = self.db.get_rentals_count(status=status, search=search)

        self.table.setRowCount(0)
        self.rental_ids = []
        today = date.today().isoformat()

        for r in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.table.setRowHeight(i, 82)
            self.rental_ids.append(r['id'])

            st = r['status']
            is_overdue = (st == 'overdue') or (st == 'active' and r['expected_return_date'] < today)
            row_color = "#FFF5F5" if is_overdue else None

            vals = [str(r['id']), r['customer_name'], r['dress_name'],
                    r['rental_date'], r['expected_return_date'],
                    f"{r['total_amount']:,.0f} ج",
                    f"{r['paid_amount']:,.0f} ج",
                    f"{r['remaining_amount']:,.0f} ج"]
            for col, v in enumerate(vals):
                if col >= 3:
                    table_col = col + 1
                else:
                    table_col = col
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if row_color: item.setBackground(QColor(row_color))
                self.table.setItem(i, table_col, item)
            self.table.setCellWidget(i, 3, self._image_cell(r['dress_image_path']))

            status_item = QTableWidgetItem(STATUS_AR.get(st, st))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            color = STATUS_COLOR.get(st, '#000')
            status_item.setForeground(QColor(color))
            status_item.setBackground(QColor(color + "22"))
            self.table.setItem(i, 9, status_item)

        total_pages = (total_count + self.items_per_page - 1) // self.items_per_page
        if total_pages == 0: total_pages = 1
        self.page_lbl.setText(f"صفحة {self.current_page} من {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)
        self.count_lbl.setText(f"إجمالي: {total_count} تأجير")

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def next_page(self):
        self.current_page += 1
        self.load_data()

    def _on_cell_double_click(self, row, col):
        if col != 3 or row < 0 or row >= len(self.rental_ids):
            return
        rental = self.db.get_rental(self.rental_ids[row])
        full = resolve_image_path(rental["image_path"] if rental else None)
        if not full:
            QMessageBox.information(self, "تنبيه", "لا توجد صورة لهذا الفستان")
            return
        ImageViewerDialog(self, full, f"صورة الفستان: {rental['dress_name']}").exec()

    def _selected_rental(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.rental_ids):
            QMessageBox.information(self, "تنبيه", "يرجى اختيار تأجير أولاً")
            return None
        return self.db.get_rental(self.rental_ids[row])

    def add_rental(self):
        dlg = NewRentalDialog(self, self.db)
        if dlg.exec():
            data = dlg.get_data()
            rid = self.db.add_rental(**data)
            self.load_data()
            row = next((i for i, x in enumerate(self.rental_ids) if x == rid), -1)
            after_save(self, self.table, row, f"تم تسجيل التأجير بنجاح.\nرقم التأجير: {rid}")
            
            from ui.owner_notify import notify_owner_action
            rental_record = self.db.get_rental(rid)
            if rental_record:
                notify_owner_action(self.db, "تأجير جديد", dict(rental_record))

    def edit_rental(self):
        rental = self._selected_rental()
        if not rental: return
        if rental['status'] == 'returned' or rental['status'] == 'cancelled':
            QMessageBox.warning(self, "تنبيه", "لا يمكن تعديل عملية منتهية أو ملغاة")
            return
            
        dlg = NewRentalDialog(self, self.db, rental)
        if dlg.exec():
            data = dlg.get_data()
            ok, err = self.db.update_rental(rental['id'], **data)
            if not ok:
                QMessageBox.warning(self, "تنبيه", err or "تعذر تحديث التأجير")
                return
            rid = rental['id']
            self.load_data()
            row = next((i for i, x in enumerate(self.rental_ids) if x == rid), -1)
            after_save(self, self.table, row, f"تم تحديث بيانات التأجير رقم {rid} بنجاح.")

    def return_dress(self):
        rental = self._selected_rental()
        if not rental: return
        if rental['status'] not in ('active', 'overdue'):
            QMessageBox.warning(self, "تنبيه", "هذا التأجير غير نشط"); return
        dlg = ReturnDialog(self, self.db, rental)
        if dlg.exec():
            data = dlg.get_data()
            self.db.return_dress(rental['id'], data['actual_return_date'],
                                 data['additional_payment'], data['method'])
            rid = rental['id']
            self.load_data()
            row = next((i for i, x in enumerate(self.rental_ids) if x == rid), -1)
            after_save(self, self.table, row, f"تم تسجيل إرجاع التأجير رقم {rid} بنجاح.")

    def add_payment(self):
        rental = self._selected_rental()
        if not rental: return
        if rental['status'] not in ('active', 'overdue'):
            QMessageBox.warning(self, "تنبيه", "لا يمكن إضافة دفعة لهذا التأجير"); return

        from PyQt6.QtWidgets import QInputDialog
        amount, ok = QInputDialog.getDouble(self, "إضافة دفعة",
                                             f"المتبقي: {rental['remaining_amount']:,.0f} جنيه\nالمبلغ:",
                                             min=0, max=999999, decimals=0)
        if ok and amount > 0:
            pid = self.db.add_payment(rental['id'], amount)
            if pid is None:
                QMessageBox.warning(self, "تنبيه", "لا يمكن إضافة دفعة أكبر من المتبقي")
                return
            self.load_data()

    def cancel_rental(self):
        rental = self._selected_rental()
        if not rental: return
        if rental['status'] not in ('active', 'overdue'):
            QMessageBox.warning(self, "تنبيه", "لا يمكن إلغاء هذا التأجير"); return
        reply = QMessageBox.question(self, "تأكيد الإلغاء",
                                     "هل تريد إلغاء هذا التأجير؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.cancel_rental(rental['id'])
            self.load_data()

    def delete_rental(self):
        rental = self._selected_rental()
        if not rental: return
        reply = QMessageBox.question(self, "تأكيد الحذف",
                                     "هل أنت متأكد أنك تريد حذف هذا التأجير نهائياً من النظام؟\nسيتم حذف جميع الدفعات المرتبطة به ولا يمكن التراجع عن هذا الإجراء.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if not AdminAuthDialog(self, self.db).exec():
                return
            ok, err = self.db.delete_rental(rental['id'])
            if not ok:
                QMessageBox.warning(self, "تعذر الحذف", err or "تعذر حذف التأجير")
                return
            self.load_data()
            QMessageBox.information(self, "نجاح ✅", "تم حذف التأجير وجميع دفعاته بنجاح")

    def print_invoice(self):
        rental = self._selected_rental()
        if not rental:
            return
        try:
            from ui.invoice import InvoiceDialog
            dlg = InvoiceDialog(self, self.db, rental)
            dlg.exec()
        except Exception as e:
            import traceback
            QMessageBox.critical(
                self, "خطأ في الفاتورة",
                f"حدث خطأ أثناء فتح الفاتورة:\n{str(e)}\n\n{traceback.format_exc()}"
            )
