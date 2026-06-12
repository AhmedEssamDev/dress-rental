from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
                             QComboBox, QDialog, QFormLayout, QDoubleSpinBox, QTextEdit,
                             QMessageBox, QFrame, QDialogButtonBox, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap
from styles import STATUS_AR, STATUS_COLOR, style_dialog_buttons, apply_button_style
from image_utils import resolve_image_path
from PyQt6.QtWidgets import QScrollArea

def notify_success(parent, message):
    QMessageBox.information(parent, "نجاح", message)

def focus_table_row(table, row):
    if 0 <= row < table.rowCount():
        table.selectRow(row)
        table.scrollToItem(table.item(row, 0))

def after_save(parent, table, row, message):
    notify_success(parent, message)
    focus_table_row(table, row)

class ImageViewerDialog(QDialog):
    def __init__(self, parent, image_path, title="عرض الصورة"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 500)
        lay = QVBoxLayout(self)
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(image_path)
        if not pix.isNull():
            lbl.setPixmap(pix.scaled(800, 800, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            lbl.setText("تعذر تحميل الصورة")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(lbl)
        lay.addWidget(scroll)

class AdminAuthDialog(QDialog):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("صلاحيات المدير")
        self.setFixedSize(300, 150)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        lay = QVBoxLayout(self)
        
        lay.addWidget(QLabel("يرجى إدخال كلمة المرور لتأكيد الإجراء:"))
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(self.pw_input)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._check_pw)
        btns.rejected.connect(self.reject)
        style_dialog_buttons(btns)
        lay.addWidget(btns)
        
    def _check_pw(self):
        if self.db.verify_admin_password(self.pw_input.text()):
            self.accept()
        else:
            QMessageBox.warning(self, "خطأ", "كلمة المرور غير صحيحة")


class DressDialog(QDialog):
    def __init__(self, parent, db, dress=None):
        super().__init__(parent)
        self.db = db
        self.dress = dress
        self._pending_image = None
        self._remove_image_flag = False
        self.setWindowTitle("إضافة فستان" if not dress else "تعديل فستان")
        self.setMinimumWidth(750)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build()
        if dress:
            self._fill(dress)

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(20)
        root.setContentsMargins(25, 25, 25, 20)

        # المحتوى الرئيسي (صورة + نموذج)
        main_layout = QHBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── الجانب الأيمن: صورة الفستان ──
        img_container = QVBoxLayout()
        img_container.setSpacing(12)
        
        img_frame = QFrame()
        img_frame.setObjectName("card")
        img_frame.setStyleSheet("QFrame#card { background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px; }")
        img_lay = QVBoxLayout(img_frame)
        img_lay.setContentsMargins(12, 12, 12, 12)
        
        self.preview = QLabel("لا توجد صورة")
        self.preview.setFixedSize(200, 260)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet(
            "background:#FFFFFF; border:2px dashed #CBD5E1; border-radius:10px; color:#94A3B8; font-size:12px;"
        )
        self.preview.setScaledContents(True)
        img_lay.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignCenter)
        
        img_container.addWidget(img_frame)

        img_btns = QHBoxLayout()
        img_btns.setSpacing(8)
        pick_btn = QPushButton("📷 اختيار")
        apply_button_style(pick_btn, "primary")
        pick_btn.setFixedHeight(36)
        pick_btn.clicked.connect(self._pick_image)
        
        clear_btn = QPushButton("🗑️")
        apply_button_style(clear_btn, "secondary")
        clear_btn.setFixedSize(36, 36)
        clear_btn.clicked.connect(self._on_remove_image)
        
        img_btns.addWidget(pick_btn, stretch=1)
        img_btns.addWidget(clear_btn)
        img_container.addLayout(img_btns)
        
        main_layout.addLayout(img_container)

        # ── الجانب الأيسر: بيانات الفستان ──
        form_container = QVBoxLayout()
        form_container.setSpacing(0)
        
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.code = QLineEdit(); self.code.setPlaceholderText("مثال: D001")
        self.name = QLineEdit(); self.name.setPlaceholderText("اسم الفستان")
        self.color = QLineEdit(); self.color.setPlaceholderText("اللون")
        self.category = QComboBox()
        self.category.addItems(["فساتين سهرة", "فساتين سواريه", "فساتين زفاف", "فساتين خطوبة",
                                 "فساتين أفراح", "فساتين كوكتيل", "أخرى"])
        
        price_lay = QHBoxLayout()
        self.rental_price = QDoubleSpinBox()
        self.rental_price.setRange(0, 999999); self.rental_price.setSuffix(" ج"); self.rental_price.setDecimals(0)
        price_lay.addWidget(self.rental_price)

        self.description = QTextEdit()
        self.description.setMaximumHeight(70)
        self.description.setPlaceholderText("وصف إضافي...")

        def _lbl(t):
            l = QLabel(t)
            l.setStyleSheet("font-weight: bold; color: #334155; min-width: 80px;")
            return l

        form.addRow(_lbl("الكود *:"), self.code)
        form.addRow(_lbl("الاسم *:"), self.name)
        
        form.addRow(_lbl("اللون:"), self.color)
        
        form.addRow(_lbl("التصنيف:"), self.category)
        form.addRow(_lbl("سعر الإيجار *:"), price_lay)
        form.addRow(_lbl("الوصف:"), self.description)
        
        form_container.addLayout(form)
        main_layout.addLayout(form_container, stretch=1)

        root.addLayout(main_layout)

        # ── الأزرار ──
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        save_lbl = "حفظ التعديلات" if self.dress else "حفظ البيانات"
        btns.button(QDialogButtonBox.StandardButton.Save).setText(save_lbl)
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        style_dialog_buttons(btns)
        root.addWidget(btns)


    def _show_preview(self, path):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.preview.setText("تعذّر تحميل الصورة")
            self.preview.setPixmap(QPixmap())
            return
        scaled = pixmap.scaled(
            self.preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview.setText("")
        self.preview.setPixmap(scaled)

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "اختيار صورة الفستان",
            "",
            "صور (*.png *.jpg *.jpeg *.webp *.bmp *.gif)",
        )
        if path:
            self._pending_image = path
            self._remove_image_flag = False
            self._show_preview(path)

    def _on_remove_image(self):
        self._pending_image = None
        self._remove_image_flag = True
        self.preview.setPixmap(QPixmap())
        self.preview.setText("لا توجد صورة")

    def _fill(self, d):
        self.code.setText(d['code'])
        self.name.setText(d['name'])
        self.color.setText(d['color'] or '')
        idx = self.category.findText(d['category'] or '')
        if idx >= 0: self.category.setCurrentIndex(idx)
        self.rental_price.setValue(d['rental_price'])
        self.description.setPlainText(d['description'] or '')
        if d['image_path']:
            full = resolve_image_path(d['image_path'])
            if full:
                self._show_preview(full)

    def _save(self):
        if not self.code.text().strip() or not self.name.text().strip():
            QMessageBox.warning(self, "تنبيه", "يرجى ملء الحقول الإلزامية (كود الفستان، الاسم، السعر)")
            return
        if self.rental_price.value() <= 0:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال سعر إيجار صحيح")
            return
        self.accept()

    def get_data(self):
        return {
            'code': self.code.text().strip(),
            'name': self.name.text().strip(),
            'size': '',
            'color': self.color.text().strip(),
            'category': self.category.currentText(),
            'rental_price': self.rental_price.value(),
            'deposit': 0,
            'description': self.description.toPlainText().strip(),
        }

    def get_pending_image(self):
        return self._pending_image

    def should_clear_image(self):
        return self._remove_image_flag


class DressesWidget(QWidget):
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
        title = QLabel("إدارة الفساتين")
        title.setObjectName("page_title")
        hdr.addWidget(title)
        hdr.addStretch()
        add_btn = QPushButton("➕  إضافة فستان جديد")
        apply_button_style(add_btn, "primary")
        add_btn.clicked.connect(self.add_dress)
        hdr.addWidget(add_btn)
        root.addLayout(hdr)

        # Stats bar
        self.stats_bar = QHBoxLayout()
        self.stats_bar.setSpacing(10)
        root.addLayout(self.stats_bar)

        # Filters
        filters = QHBoxLayout(); filters.setSpacing(10)
        self.search = QLineEdit()
        self.search.setObjectName("search_bar")
        self.search.setPlaceholderText("🔍  بحث بالاسم أو الكود أو اللون...")
        self.search.setFixedWidth(300)
        self.search.textChanged.connect(self.load_data)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["الكل", "متاحة", "مؤجرة", "صيانة"])
        self.status_filter.currentIndexChanged.connect(self.load_data)
        self.status_filter.setFixedWidth(150)

        filters.addWidget(self.search)
        filters.addWidget(QLabel("الحالة:"))
        filters.addWidget(self.status_filter)
        filters.addStretch()
        root.addLayout(filters)

        # Table
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(["الكود", "الاسم", "المقاس", "اللون",
                                               "التصنيف", "مرات التأجير", "سعر الإيجار", "التأمين", "صورة", "الحالة"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_double_click)
        self.table.cellDoubleClicked.connect(self._on_cell_double_click)
        root.addWidget(self.table)

        # Action buttons
        action = QHBoxLayout(); action.setSpacing(10)
        edit_btn = QPushButton("✏️  تعديل")
        apply_button_style(edit_btn, "warning")
        edit_btn.clicked.connect(self.edit_dress)
        del_btn = QPushButton("🗑️  حذف")
        apply_button_style(del_btn, "danger")
        del_btn.clicked.connect(self.archive_dress)
        maint_btn = QPushButton("🔧  وضع صيانة")
        apply_button_style(maint_btn, "secondary")
        maint_btn.clicked.connect(self.toggle_maintenance)
        action.addWidget(edit_btn)
        action.addWidget(del_btn)
        action.addWidget(maint_btn)
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

        self.dress_ids = []

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

    def _apply_dress_image(self, did, dlg):
        if dlg.should_clear_image():
            self.db.clear_dress_image(did)
        elif dlg.get_pending_image():
            self.db.set_dress_image(did, dlg.get_pending_image())

    def _update_stats(self):
        for i in reversed(range(self.stats_bar.count())):
            w = self.stats_bar.itemAt(i).widget()
            if w: w.deleteLater()

        dresses = self.db.get_all_dresses()
        statuses = {}
        for d in dresses:
            statuses[d['status']] = statuses.get(d['status'], 0) + 1

        chips = [
            ("الكل", len(dresses), "#4F6AFF"),
            ("متاح", statuses.get('available', 0), "#10B981"),
            ("مؤجر", statuses.get('rented', 0), "#F59E0B"),
            ("صيانة", statuses.get('maintenance', 0), "#EF4444"),
        ]
        for label, count, color in chips:
            lbl = QLabel(f"  {label}: {count}  ")
            lbl.setStyleSheet(f"background:{color}22; color:{color}; border-radius:12px; "
                              f"padding:4px 12px; font-weight:bold; font-size:12px;")
            self.stats_bar.addWidget(lbl)
        self.stats_bar.addStretch()

    def load_data(self):
        self._update_stats()
        status_map = {0: None, 1: 'available', 2: 'rented', 3: 'maintenance'}
        status = status_map.get(self.status_filter.currentIndex())
        search = self.search.text().strip() or None
        
        offset = (self.current_page - 1) * self.items_per_page
        rows = self.db.get_all_dresses(status=status, search=search, limit=self.items_per_page, offset=offset)
        total_count = self.db.get_dresses_count(status=status, search=search)

        self.table.setRowCount(0)
        self.dress_ids = []
        for d in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.table.setRowHeight(i, 82)
            self.dress_ids.append(d['id'])

            vals = [d['code'], d['name'], d['size'] or '—', d['color'] or '—',
                    d['category'] or '—', str(d['rental_count']), f"{d['rental_price']:,.0f} ج",
                    f"{d['deposit'] or 0:,.0f} ج"]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, col, item)

            self.table.setCellWidget(i, 8, self._image_cell(d['image_path']))

            # Status badge
            st = d['status']
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
        self.count_lbl.setText(f"إجمالي: {total_count} فستان")

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def next_page(self):
        self.current_page += 1
        self.load_data()

    def _selected_row(self):
        rows = self.table.selectedItems()
        if not rows:
            return None, None
        row = self.table.currentRow()
        if row < 0 or row >= len(self.dress_ids):
            return None, None
        return row, self.dress_ids[row]

    def _on_double_click(self, index):
        self.edit_dress()

    def _on_cell_double_click(self, row, col):
        if col != 8 or row < 0 or row >= len(self.dress_ids):
            return
        dress = self.db.get_dress(self.dress_ids[row])
        full = resolve_image_path(dress["image_path"] if dress else None)
        if not full:
            QMessageBox.information(self, "تنبيه", "لا توجد صورة لهذا الفستان")
            return
        ImageViewerDialog(self, full, f"صورة الفستان: {dress['name']}").exec()

    def add_dress(self):
        dlg = DressDialog(self, self.db)
        if dlg.exec():
            data = dlg.get_data()
            result = self.db.add_dress(**data)
            if result is None:
                QMessageBox.warning(self, "خطأ", f"الكود '{data['code']}' مستخدم مسبقاً")
            else:
                self._apply_dress_image(result, dlg)
                self.load_data()
                row = len(self.dress_ids) - 1
                for i, did in enumerate(self.dress_ids):
                    if did == result:
                        row = i
                        break
                after_save(self, self.table, row, f"تم إضافة الفستان «{data['name']}» بنجاح.")

    def edit_dress(self):
        row, did = self._selected_row()
        if did is None:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار فستان أولاً")
            return
        dress = self.db.get_dress(did)
        if dress['status'] == 'rented':
            QMessageBox.warning(self, "تنبيه", "لا يمكن تعديل فستان مؤجر حالياً")
            return
        dlg = DressDialog(self, self.db, dress)
        if dlg.exec():
            data = dlg.get_data()
            self.db.update_dress(did, **data)
            self._apply_dress_image(did, dlg)
            self.load_data()
            row = self._row_for_id(did)
            after_save(self, self.table, row, f"تم تحديث بيانات الفستان «{data['name']}» بنجاح.")

    def archive_dress(self):
        row, did = self._selected_row()
        if did is None:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار فستان أولاً")
            return
        dress = self.db.get_dress(did)
        if dress['status'] == 'rented':
            QMessageBox.warning(self, "خطأ", "لا يمكن حذف فستان مؤجر حالياً")
            return
        reply = QMessageBox.question(self, "تأكيد الحذف",
                                     f"هل أنت متأكد أنك تريد حذف الفستان «{dress['name']}»؟\n\n"
                                     "ملاحظة: سيتم حذف الفستان من القوائم فقط\nولن يتم إتلاف الفواتير أو السجلات المرتبطة به.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if not AdminAuthDialog(self, self.db).exec():
                return
            ok, err = self.db.archive_dress(did)
            if not ok:
                QMessageBox.warning(self, "تعذر الحذف", err or "لا يمكن حذف الفستان حالياً")
                return
            self.load_data()

    def toggle_maintenance(self):
        row, did = self._selected_row()
        if did is None:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار فستان أولاً")
            return
        dress = self.db.get_dress(did)
        if dress['status'] == 'rented':
            QMessageBox.warning(self, "خطأ", "الفستان مؤجر حالياً")
            return
        new_status = 'available' if dress['status'] == 'maintenance' else 'maintenance'
        self.db.update_dress_status(did, new_status)
        self.load_data()
        row = self._row_for_id(did)
        label = "متاح" if new_status == 'available' else "صيانة"
        notify_success(self, f"تم تغيير حالة الفستان «{dress['name']}» إلى: {label}")
        focus_table_row(self.table, row)

    def _row_for_id(self, did):
        for i, dress_id in enumerate(self.dress_ids):
            if dress_id == did:
                return i
        return -1
