import os
from datetime import date
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem,
                             QStackedWidget, QLineEdit, QDialog, QFormLayout,
                             QMessageBox, QDateEdit, QGraphicsDropShadowEffect,
                             QTextEdit, QDoubleSpinBox, QComboBox)
from PyQt6.QtCore import Qt, QSize, QDate, QRect, QPointF
from PyQt6.QtGui import QColor, QPixmap, QIcon, QPainter, QBrush, QPen, QTextDocument, QPainterPath, QLinearGradient
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog

from image_utils import resolve_image_path
from styles import apply_button_style, style_dialog_buttons

class SimpleInvoiceDialog(QDialog):
    def __init__(self, parent, rental_data):
        super().__init__(parent)
        self.rental_data = rental_data
        self.setWindowTitle("طباعة إيصال التأجير")
        self.setMinimumSize(400, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        
        btns = QHBoxLayout()
        print_btn = QPushButton("🖨️  معاينة الطباعة")
        apply_button_style(print_btn, "primary")
        print_btn.clicked.connect(self._print_preview)
        
        close_btn = QPushButton("إغلاق")
        apply_button_style(close_btn, "secondary")
        close_btn.clicked.connect(self.accept)
        
        btns.addWidget(print_btn)
        btns.addStretch()
        btns.addWidget(close_btn)
        
        lay.addLayout(btns)
        
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setHtml(self._generate_html())
        lay.addWidget(self.preview)

    def _generate_html(self):
        r = self.rental_data
        
        import base64
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "logo.jpeg")
        img_tag = ""
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as img_file:
                b64 = base64.b64encode(img_file.read()).decode('utf-8')
                img_tag = f'<div style="text-align: center; margin-bottom: 10px;"><img src="data:image/jpeg;base64,{b64}" width="120"></div>'

        html = f"""
        <html dir="rtl">
        <head>
        <style>
            body {{ font-family: 'Arial'; margin: 0; padding: 10px; direction: rtl; text-align: right; color: #000; width: 280px; font-size: 14px; }}
            .header {{ text-align: center; border-bottom: 1px dashed #000; padding-bottom: 10px; margin-bottom: 10px; }}
            .header h2 {{ font-size: 16px; margin: 5px 0; }}
            .header p {{ font-size: 12px; margin: 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; direction: rtl; }}
            td {{ padding: 5px; font-size: 13px; vertical-align: top; text-align: right; }}
            .bold {{ font-weight: bold; white-space: nowrap; width: 40%; text-align: right; }}
            .footer {{ text-align: center; margin-top: 15px; font-size: 12px; border-top: 1px dashed #000; padding-top: 10px; }}
        </style>
        </head>
        <body>
            {img_tag}
            <div class="header">
                <h2>نظام تأجير الفساتين</h2>
                <p>إيصال تأجير فستان</p>
                <p>التاريخ: {date.today().strftime('%Y-%m-%d')}</p>
            </div>
            <table>
                <tr><td style="text-align: right;">{r.get('customer_name', '')}</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">العميل</td></tr>
                <tr><td style="text-align: right;">{r.get('customer_phone', '')}</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">الهاتف</td></tr>
                <tr><td style="text-align: right;">{r.get('dress_name', '')} ({r.get('dress_code', '')})</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">الفستان</td></tr>
                <tr><td style="text-align: right;">{r.get('rental_date', '')}</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">الاستلام</td></tr>
                <tr><td style="text-align: right;">{r.get('return_date', '')}</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">الإرجاع</td></tr>
                <tr><td style="text-align: right;">{r.get('total_amount', 0)} جنيه</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">الإجمالي</td></tr>
                <tr><td style="text-align: right;">{r.get('paid_amount', 0)} جنيه</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">المدفوع</td></tr>
                <tr><td style="text-align: right;">{r.get('remaining_amount', 0)} جنيه</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">المتبقي</td></tr>
                <tr><td style="text-align: right;">{r.get('registrar_name', 'غير محدد')}</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">الكاشير</td></tr>
            </table>
            <div class="footer">
                شكراً لتعاملكم معنا!<br>يُرجى الالتزام بموعد الإرجاع.
            </div>
        </body>
        </html>
        """
        return html

    def _print_preview(self):
        printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        from PyQt6.QtGui import QPageSize
        from PyQt6.QtCore import QSizeF
        # Set 80mm width page size
        printer.setPageSize(QPageSize(QSizeF(80, 200), QPageSize.Unit.Millimeter))
        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowTitle("معاينة الطباعة")
        preview.paintRequested.connect(self._do_print)
        preview.exec()

    def _do_print(self, printer):
        doc = QTextDocument()
        doc.setHtml(self._generate_html())
        doc.print(printer)

class SimpleRentalDialog(QDialog):
    def __init__(self, parent, db, dress):
        super().__init__(parent)
        self.db = db
        self.dress = dress
        self.setWindowTitle(f"تأجير/حجز فستان: {dress['name']}")
        self.setMinimumWidth(400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        form = QFormLayout()
        
        self.cust_name = QLineEdit()
        self.cust_name.setPlaceholderText("اسم العميل")
        
        self.cust_phone = QLineEdit()
        self.cust_phone.setPlaceholderText("رقم الهاتف")
        
        self.rent_date = QDateEdit()
        self.rent_date.setDate(QDate.currentDate())
        self.rent_date.setCalendarPopup(True)
        self.rent_date.setDisplayFormat("dd/MM/yyyy")
        
        self.return_date = QDateEdit()
        self.return_date.setDate(QDate.currentDate().addDays(3))
        self.return_date.setCalendarPopup(True)
        self.return_date.setDisplayFormat("dd/MM/yyyy")
        
        self.paid_amount = QDoubleSpinBox()
        self.paid_amount.setMaximum(100000)
        self.paid_amount.setDecimals(2)
        # set default to 0 so the user enters it manually
        self.paid_amount.setValue(0.0)
        
        self.registrar_combo = QComboBox()
        self.registrar_combo.setEditable(True)
        self.registrar_combo.lineEdit().setPlaceholderText("أدخل اسم الكاشير")
        self._load_registrars()
        
        form.addRow("اسم العميل:", self.cust_name)
        form.addRow("رقم الهاتف:", self.cust_phone)
        form.addRow("تاريخ الاستلام:", self.rent_date)
        form.addRow("موعد الإرجاع:", self.return_date)
        form.addRow("المبلغ المدفوع (جنيه):", self.paid_amount)
        form.addRow("الموظف (الكاشير):", self.registrar_combo)
        
        lay.addLayout(form)
        
        from PyQt6.QtWidgets import QDialogButtonBox
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("تأكيد التأجير")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        style_dialog_buttons(btns)
        lay.addWidget(btns)

    def _load_registrars(self):
        self.registrar_combo.clear()
        regs = self.db.conn.execute("SELECT id, name FROM registrars WHERE is_archived=0 ORDER BY name").fetchall()
        for r in regs:
            self.registrar_combo.addItem(r['name'], r['id'])
        self.registrar_combo.setCurrentIndex(-1)

    def _accept(self):
        if not self.cust_name.text().strip():
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال اسم العميل.")
            return
        
        # Add simple customer
        cid = self.db.add_customer(
            name=self.cust_name.text().strip(),
            phone=self.cust_phone.text().strip(),
            phone2="", address="", id_number=""
        )
        
        paid = self.paid_amount.value()
        total = float(self.dress.get('rental_price', 0) or 0)
        remaining = max(0, total - paid)
        
        reg_id = self.registrar_combo.currentData()
        reg_name = self.registrar_combo.currentText().strip()
        
        # If the user typed a new name that isn't in the DB, let's just insert it and get its ID
        if reg_name and not reg_id:
            existing = self.db.conn.execute("SELECT id FROM registrars WHERE name=?", (reg_name,)).fetchone()
            if existing:
                reg_id = existing['id']
            else:
                c = self.db.conn.cursor()
                c.execute("INSERT INTO registrars (name, phone) VALUES (?, '')", (reg_name,))
                self.db.conn.commit()
                reg_id = c.lastrowid
        
        # Add rental with money values
        rid = self.db.add_rental(
            dress_id=self.dress['id'],
            customer_id=cid,
            rental_date=self.rent_date.date().toString("yyyy-MM-dd"),
            expected_return_date=self.return_date.date().toString("yyyy-MM-dd"),
            rental_price=total, deposit=0, discount=0, total_amount=total, paid_amount=paid,
            registered_by_id=reg_id
        )
        
        self.rental_data = {
            'id': rid,
            'customer_name': self.cust_name.text().strip(),
            'customer_phone': self.cust_phone.text().strip(),
            'dress_name': self.dress['name'],
            'dress_code': self.dress['code'],
            'dress_color': self.dress['color'],
            'dress_size': self.dress['size'],
            'rental_date': self.rent_date.date().toString("yyyy-MM-dd"),
            'return_date': self.return_date.date().toString("yyyy-MM-dd"),
            'total_amount': total,
            'paid_amount': paid,
            'remaining_amount': remaining,
            'registrar_name': reg_name
        }
        
        # WhatsApp notification
        try:
            from ui.owner_notify import notify_owner_action
            notify_owner_action(
                db=self.db,
                action_type='تأجير جديد',
                record=self.rental_data
            )
        except Exception as e:
            print("WhatsApp error:", e)
        
        self.accept()

class MonthlyRentalChartWidget(QWidget):
    """رسم بياني يوضح عدد التأجيرات لكل شهر للفساتين."""
    
    MONTH_NAMES = {
        '01': 'يناير', '02': 'فبراير', '03': 'مارس', '04': 'أبريل',
        '05': 'مايو', '06': 'يونيو', '07': 'يوليو', '08': 'أغسطس',
        '09': 'سبتمبر', '10': 'أكتوبر', '11': 'نوفمبر', '12': 'ديسمبر',
    }
    
    def __init__(self, month_counts: dict):
        super().__init__()
        self.month_counts = month_counts
        self.setFixedHeight(160)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        
        # خلفية مع إطار
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(QColor("#E2E8F0"), 1))
        painter.drawRoundedRect(1, 1, w - 2, h - 2, 12, 12)
        
        # عنوان الرسم البياني
        title_font = painter.font()
        title_font.setBold(True)
        title_font.setPointSize(12)
        painter.setFont(title_font)
        painter.setPen(QColor("#1E293B"))
        total = sum(self.month_counts.values())
        painter.drawText(QRect(0, 10, w, 30), Qt.AlignmentFlag.AlignCenter, f"({total}) 📊 عدد التأجيرات لكل شهر")
        
        # إعداد البيانات
        months = sorted(self.month_counts.keys())
        counts = [self.month_counts[m] for m in months]
        max_count = max(counts) if counts else 0
        
        if not months or max_count == 0:
            # لا توجد بيانات
            no_data_font = painter.font()
            no_data_font.setPointSize(11)
            no_data_font.setBold(False)
            painter.setFont(no_data_font)
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "لا توجد تأجيرات بعد")
            painter.end()
            return
        
        # حدود الرسم
        top_margin = 40
        bottom_margin = 40
        side_margin = 40
        chart_h = h - top_margin - bottom_margin
        chart_w = w - 2 * side_margin
        
        # حساب مواقع النقاط
        n = len(months)
        gap = 12
        point_spacing = min(60, max(30, (chart_w - (n - 1) * gap) // n if n > 0 else 0))
        total_chart_width = n * point_spacing
        start_x = side_margin + (chart_w - total_chart_width) // 2
        
        base_y = h - bottom_margin
        
        points = []
        for i, month in enumerate(months):
            cnt = self.month_counts[month]
            height_ratio = cnt / max_count if max_count > 0 else 0
            point_h = int(chart_h * height_ratio)
            x = start_x + i * point_spacing + (point_spacing // 2)
            y = base_y - point_h
            points.append(QPointF(x, y))
            
        # رسم المنطقة المظللة تحت الخط
        if len(points) > 0:
            path = QPainterPath()
            path.moveTo(points[0].x(), base_y)
            for pt in points:
                path.lineTo(pt)
            path.lineTo(points[-1].x(), base_y)
            path.closeSubpath()
            
            grad = QLinearGradient(0, top_margin, 0, base_y)
            grad.setColorAt(0.0, QColor(59, 130, 246, 100)) # أزرق شفاف
            grad.setColorAt(1.0, QColor(59, 130, 246, 10))  # شبه شفاف جدا
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(path)
            
            # رسم الخط (السهم/المسار)
            line_path = QPainterPath()
            line_path.moveTo(points[0])
            for pt in points[1:]:
                line_path.lineTo(pt)
            
            pen = QPen(QColor("#3B82F6"), 3)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(line_path)
            
            # رسم النقاط والتسميات
            for i, pt in enumerate(points):
                cnt = self.month_counts[months[i]]
                
                # رسم النقطة (دائرة صغيرة)
                painter.setPen(QPen(QColor("#FFFFFF"), 2))
                painter.setBrush(QBrush(QColor("#2563EB")))
                painter.drawEllipse(pt, 5, 5)
                
                # اسم الشهر تحت الرسم
                month = months[i]
                month_num = month[5:7] if len(month) >= 7 else month[5:]
                month_name = self.MONTH_NAMES.get(month_num, month_num)
                label_font = painter.font()
                label_font.setBold(False)
                label_font.setPointSize(8)
                painter.setFont(label_font)
                painter.setPen(QColor("#64748B"))
                painter.drawText(QRect(int(pt.x()) - 30, base_y + 5, 60, 18), Qt.AlignmentFlag.AlignCenter, month_name)
                # السنة
                year = month[:4]
                painter.drawText(QRect(int(pt.x()) - 30, base_y + 20, 60, 16), Qt.AlignmentFlag.AlignCenter, year)
        
        # خط القاعدة
        painter.setPen(QPen(QColor("#CBD5E1"), 2))
        painter.drawLine(side_margin, base_y, w - side_margin, base_y)
        
        painter.end()


class DressDetailsWidget(QWidget):
    def __init__(self, db, back_callback):
        super().__init__()
        self.db = db
        self.back_callback = back_callback
        self.dress = None
        self._build_ui()

    def _build_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(20, 20, 20, 20)
        
        # Header
        hdr = QHBoxLayout()
        back_btn = QPushButton("◀ عودة")
        apply_button_style(back_btn, "secondary")
        back_btn.clicked.connect(self.back_callback)
        hdr.addWidget(back_btn)
        hdr.addStretch()
        main_lay.addLayout(hdr)
        
        # Content
        content_lay = QHBoxLayout()
        
        # Right: Image
        self.img_lbl = QLabel()
        self.img_lbl.setFixedSize(300, 400)
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_lbl.setStyleSheet("background:#FFF; border:2px dashed #CBD5E1; border-radius:10px;")
        content_lay.addWidget(self.img_lbl)
        
        # Left: Details & Chart & Buttons
        left_lay = QVBoxLayout()
        self.title_lbl = QLabel()
        self.title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E293B;")
        left_lay.addWidget(self.title_lbl)
        
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet("font-size: 16px; color: #475569;")
        left_lay.addWidget(self.info_lbl)
        
        left_lay.addSpacing(20)
        
        # Chart placeholder
        self.chart_container = QVBoxLayout()
        left_lay.addLayout(self.chart_container)
        
        left_lay.addStretch()
        
        # حالة الحجز
        self.status_lbl = QLabel()
        self.status_lbl.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px 16px; border-radius: 8px;")
        left_lay.addWidget(self.status_lbl)
        
        left_lay.addSpacing(10)
        
        # Buttons
        btns = QHBoxLayout()
        self.action_btn = QPushButton("✅  تأجير / حجز")
        apply_button_style(self.action_btn, "primary")
        self.action_btn.setFixedHeight(50)
        self.action_btn.clicked.connect(self._on_main_action)
        
        self.print_btn = QPushButton("🖨️ طباعة إيصال")
        apply_button_style(self.print_btn, "secondary")
        self.print_btn.setFixedHeight(50)
        self.print_btn.clicked.connect(self._on_print)
        
        btns.addWidget(self.action_btn, stretch=2)
        btns.addWidget(self.print_btn, stretch=1)
        left_lay.addLayout(btns)
        
        # أزرار التعديل والحذف
        mgmt_btns = QHBoxLayout()
        self.edit_btn = QPushButton("✏️ تعديل الفستان")
        apply_button_style(self.edit_btn, "warning")
        self.edit_btn.setFixedHeight(45)
        self.edit_btn.clicked.connect(self._on_edit)
        
        self.delete_btn = QPushButton("🗑️ حذف الفستان")
        apply_button_style(self.delete_btn, "danger")
        self.delete_btn.setFixedHeight(45)
        self.delete_btn.clicked.connect(self._on_delete)
        
        mgmt_btns.addWidget(self.edit_btn)
        mgmt_btns.addWidget(self.delete_btn)
        left_lay.addLayout(mgmt_btns)
        
        content_lay.addLayout(left_lay, stretch=1)
        main_lay.addLayout(content_lay)

    def set_dress(self, dress_id):
        dress_row = self.db.get_dress(dress_id)
        if not dress_row: return
        self.dress = dict(dress_row)
        
        self.title_lbl.setText(f"{self.dress['name']} (كود: {self.dress['code']})")
        
        info = f"اللون: {self.dress.get('color') or '—'}\n"
        info += f"التصنيف: {self.dress.get('category') or '—'}\n"
        price = self.dress.get('rental_price', 0) or 0
        info += f"السعر: {price} جنيه\n"
        
        # حالة الحجز وتحديث الأزرار
        status = self.dress.get('status', 'available')
        
        if status == 'rented':
            active_rental = self.db.conn.execute(
                "SELECT r.*, c.name as customer_name FROM rentals r JOIN customers c ON r.customer_id=c.id "
                "WHERE r.dress_id=? AND r.status='active' ORDER BY r.rental_date DESC LIMIT 1",
                (self.dress['id'],)
            ).fetchone()
            if active_rental:
                info += f"\n-- تفاصيل التأجير النشط --\n"
                info += f"العميل: {active_rental['customer_name']}\n"
                info += f"الاستلام: {active_rental['rental_date']}\n"
                info += f"الإرجاع: {active_rental['expected_return_date']}\n"
                info += f"الإجمالي: {active_rental['total_amount'] or 0} ج | المدفوع: {active_rental['paid_amount'] or 0} ج"
                
        self.info_lbl.setText(info)
        if status == 'rented':
            self.status_lbl.setText("📛 محجوز حالياً")
            self.status_lbl.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px 16px; border-radius: 8px; background: #FEE2E2; color: #DC2626;")
            self.action_btn.setText("↩️ إرجاع الفستان")
            apply_button_style(self.action_btn, "warning")
            self.print_btn.setEnabled(True)
        else:
            self.status_lbl.setText("✅ متاح للحجز")
            self.status_lbl.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px 16px; border-radius: 8px; background: #D1FAE5; color: #059669;")
            self.action_btn.setText("✅ تأجير / حجز")
            apply_button_style(self.action_btn, "primary")
            self.print_btn.setEnabled(False)
        
        full_img = resolve_image_path(self.dress['image_path'])
        if full_img:
            pix = QPixmap(full_img)
            self.img_lbl.setPixmap(pix.scaled(self.img_lbl.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.img_lbl.setText("لا توجد صورة")
            self.img_lbl.setPixmap(QPixmap())
            
        # Draw Chart
        for i in reversed(range(self.chart_container.count())): 
            w = self.chart_container.itemAt(i).widget()
            if w: w.deleteLater()
            
        # Get count of rentals
        rows = self.db.conn.execute(
            "SELECT strftime('%Y-%m', rental_date) as month, COUNT(*) as cnt FROM rentals WHERE dress_id=? GROUP BY month ORDER BY month"
            , (dress_id,)
        ).fetchall()
        month_counts = {row['month']: row['cnt'] for row in rows}
        chart = MonthlyRentalChartWidget(month_counts)
        self.chart_container.addWidget(chart)

    def _on_main_action(self):
        status = self.dress.get('status', 'available')
        
        if status == 'rented':
            # ارجاع الفستان
            reply = QMessageBox.question(self, "تأكيد الإرجاع", "هل أنت متأكد من استلام الفستان وإرجاعه للمخزون؟",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                rental = self.db.conn.execute(
                    "SELECT id FROM rentals WHERE dress_id=? AND status='active' ORDER BY rental_date DESC LIMIT 1", 
                    (self.dress['id'],)
                ).fetchone()
                if rental:
                    self.db.return_dress(rental['id'], QDate.currentDate().toString("yyyy-MM-dd"))
                    QMessageBox.information(self, "نجاح", "تم إرجاع الفستان بنجاح وأصبح متاحاً.")
                    self.set_dress(self.dress['id'])
                else:
                    # In case of missing rental record, just force status change
                    self.db.update_dress_status(self.dress['id'], 'available')
                    self.set_dress(self.dress['id'])
                    
        else:
            # تأجير الفستان
            dlg = SimpleRentalDialog(self, self.db, self.dress)
            if dlg.exec():
                inv = SimpleInvoiceDialog(self, dlg.rental_data)
                inv.exec()
                self.back_callback()  # return to grid

    def _on_print(self):
        # Fetch most recent rental for this dress
        rental = self.db.conn.execute(
            "SELECT r.*, c.name as customer_name, c.phone as customer_phone, reg.name as registrar_name "
            "FROM rentals r JOIN customers c ON r.customer_id = c.id "
            "LEFT JOIN registrars reg ON r.registered_by_id = reg.id "
            "WHERE r.dress_id=? ORDER BY r.rental_date DESC LIMIT 1",
            (self.dress['id'],)
        ).fetchone()
        if not rental:
            QMessageBox.information(self, "تنبيه", "لا توجد سجلات تأجير سابقة لهذا الفستان لطباعتها.")
            return
        data = {
            'id': rental['id'],
            'customer_name': rental['customer_name'],
            'customer_phone': rental['customer_phone'],
            'dress_name': self.dress['name'],
            'dress_code': self.dress['code'],
            'dress_color': self.dress['color'],
            'dress_size': self.dress['size'],
            'rental_date': rental['rental_date'],
            'return_date': rental['expected_return_date'],
            'total_amount': rental['total_amount'] or 0,
            'paid_amount': rental['paid_amount'] or 0,
            'remaining_amount': rental['remaining_amount'] or 0,
            'registrar_name': rental['registrar_name'] or 'غير محدد'
        }
        inv = SimpleInvoiceDialog(self, data)
        inv.exec()

    def _on_edit(self):
        # Open DressDialog in edit mode
        from ui.dresses import DressDialog
        dlg = DressDialog(self, self.db, self.dress)
        if dlg.exec():
            data = dlg.get_data()
            self.db.update_dress(self.dress['id'], **data)
            # Update image if changed
            if dlg.get_pending_image():
                self.db.set_dress_image(self.dress['id'], dlg.get_pending_image())
            self.set_dress(self.dress['id'])
            QMessageBox.information(self, "نجاح", "تم تعديل الفستان بنجاح.")

    def _on_delete(self):
        reply = QMessageBox.question(self, "تأكيد الحذف",
                                     f"هل أنت متأكد أنك تريد حذف الفستان «{self.dress['name']}»؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            ok, err = self.db.delete_dress(self.dress['id'])
            if ok:
                QMessageBox.information(self, "نجاح", "تم حذف الفستان.")
                self.back_callback()
            else:
                if "مرتبط بالسجلات" in err:
                    force_reply = QMessageBox.warning(self, "تأكيد الحذف النهائي",
                                                err + "\n\nهل أنت متأكد من حذف الفستان ومسح جميع السجلات المرتبطة به نهائياً؟",
                                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if force_reply == QMessageBox.StandardButton.Yes:
                        ok_force, err_force = self.db.delete_dress(self.dress['id'], force=True)
                        if ok_force:
                            QMessageBox.information(self, "نجاح", "تم حذف الفستان وجميع السجلات المرتبطة به بنجاح.")
                            self.back_callback()
                        else:
                            QMessageBox.warning(self, "خطأ", err_force or "فشل الحذف الإجباري.")
                else:
                    QMessageBox.warning(self, "خطأ", err or "لا يمكن حذف الفستان.")

class CashierGridWidget(QWidget):
    def __init__(self, db, select_callback):
        super().__init__()
        self.db = db
        self.select_callback = select_callback
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        
        # Header actions
        actions_lay = QHBoxLayout()
        
        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 بحث باسم الفستان أو الكود...")
        self.search.setStyleSheet("padding: 10px; font-size: 16px; border-radius: 8px; border: 1px solid #CBD5E1;")
        self.search.textChanged.connect(self.load_data)
        actions_lay.addWidget(self.search, stretch=1)
        
        # Add Dress Button
        self.add_btn = QPushButton("➕ إضافة فستان")
        apply_button_style(self.add_btn, "success")
        self.add_btn.setFixedHeight(45)
        self.add_btn.clicked.connect(self._on_add_dress)
        actions_lay.addWidget(self.add_btn)
        
        lay.addLayout(actions_lay)
        
        # Grid (using QListWidget IconMode)
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(150, 200))
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSpacing(20)
        self.list_widget.setStyleSheet("""
            QListWidget { background: transparent; border: none; }
            QListWidget::item { background: #FFF; border-radius: 10px; padding: 10px; }
            QListWidget::item:selected { background: #E0F2FE; border: 2px solid #3B82F6; }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        lay.addWidget(self.list_widget)

    def _on_add_dress(self):
        from ui.dresses import DressDialog
        dlg = DressDialog(self, self.db)
        if dlg.exec():
            data = dlg.get_data()
            result = self.db.add_dress(**data)
            if result is None:
                QMessageBox.warning(self, "خطأ", f"الكود '{data['code']}' مستخدم مسبقاً")
            else:
                if dlg.get_pending_image():
                    self.db.set_dress_image(result, dlg.get_pending_image())
                self.load_data()

    def load_data(self):
        self.list_widget.clear()
        search = self.search.text().strip() or None
        dresses = self.db.get_all_dresses(search=search)
        
        for d in dresses:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, d['id'])
            
            # Create icon from image
            full_img = resolve_image_path(d['image_path'])
            if full_img:
                icon = QIcon(full_img)
            else:
                # Create a blank icon
                pix = QPixmap(150, 200)
                pix.fill(QColor("#E2E8F0"))
                p = QPainter(pix)
                p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "لا صورة")
                p.end()
                icon = QIcon(pix)
                
            item.setIcon(icon)
            
            # Text
            status_ar = "متاح" if d['status'] == 'available' else ("مؤجر" if d['status'] == 'rented' else "صيانة")
            item.setText(f"{d['name']}\n{d['code']}\n({status_ar})")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.list_widget.addItem(item)

    def _on_item_clicked(self, item):
        dress_id = item.data(Qt.ItemDataRole.UserRole)
        self.select_callback(dress_id)


class CashierWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)
        
        self.grid_view = CashierGridWidget(self.db, self._show_details)
        self.details_view = DressDetailsWidget(self.db, self._show_grid)
        
        self.stack.addWidget(self.grid_view)
        self.stack.addWidget(self.details_view)

    def _show_details(self, dress_id):
        self.details_view.set_dress(dress_id)
        self.stack.setCurrentIndex(1)

    def _show_grid(self):
        self.grid_view.load_data()
        self.stack.setCurrentIndex(0)
