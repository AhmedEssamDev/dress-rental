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
                <h2>عماد جاد فاشون</h2>
                <p>إيصال تأجير فستان</p>
                <p>التاريخ: {date.today().strftime('%Y-%m-%d')}</p>
            </div>
            <table>
                <tr><td style="text-align: right;">{r.get('customer_name', '')}</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">العميل</td></tr>
                <tr><td style="text-align: right;">{r.get('customer_phone', '')}</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">الهاتف</td></tr>
                <tr><td style="text-align: right;">{r.get('dress_name', '')} ({r.get('dress_code', '')})</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">الفستان</td></tr>
                <tr><td style="text-align: right;">{r.get('rental_date', '')}</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">الاستلام</td></tr>
                <tr><td style="text-align: right;">{r.get('return_date', '')}</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">الإرجاع</td></tr>
                <tr><td style="text-align: right;">{r.get('rental_price', 0)} جنيه</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">قيمة الإيجار</td></tr>
                <tr><td style="text-align: right;">{r.get('deposit', 0)} جنيه</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">التأمين</td></tr>
                <tr><td style="text-align: right; font-weight: bold;">{r.get('total_amount', 0)} جنيه</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">الإجمالي</td></tr>
                <tr><td style="text-align: right;">{r.get('paid_amount', 0)} جنيه</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">المدفوع</td></tr>
                <tr><td style="text-align: right;">{r.get('remaining_amount', 0)} جنيه</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">المتبقي</td></tr>
                <tr><td style="text-align: right;">{r.get('registrar_name', 'غير محدد')}</td><td class="bold" style="width: 15px; text-align: center;">:</td><td class="bold">الكاشير</td></tr>
            </table>
            <div class="footer">
                شكراً لتعاملكم معنا!<br>يُرجى الالتزام بموعد الإرجاع.<br><br>
                <b>للتواصل:</b><br>
                01096078609<br>
                0552475393
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

class ReturnSettlementDialog(QDialog):
    def __init__(self, parent, db, rental):
        super().__init__(parent)
        self.db = db
        self.rental = rental
        self.setWindowTitle("تسوية الإرجاع")
        self.setMinimumWidth(400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.total_amount = float(rental['total_amount'] or 0)
        self.deposit = float(rental['deposit'] or 0)
        self.rental_price = float(rental['rental_price'] or 0)
        self.paid = float(rental['paid_amount'] or 0)
        
        self.final_collection = 0
        self.final_refund = 0
        
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        
        from PyQt6.QtWidgets import QGroupBox, QRadioButton
        info_group = QGroupBox("تفاصيل الحساب الحالية")
        info_lay = QFormLayout(info_group)
        info_lay.addRow("قيمة الإيجار:", QLabel(f"{self.rental_price} جنيه"))
        info_lay.addRow("قيمة التأمين:", QLabel(f"{self.deposit} جنيه"))
        info_lay.addRow("الإجمالي:", QLabel(f"{self.total_amount} جنيه"))
        info_lay.addRow("المدفوع مقدماً:", QLabel(f"{self.paid} جنيه"))
        lay.addWidget(info_group)
        
        condition_group = QGroupBox("حالة الفستان")
        cond_lay = QVBoxLayout(condition_group)
        self.radio_intact = QRadioButton("الفستان سليم (استرداد/إعفاء التأمين)")
        self.radio_damaged = QRadioButton("الفستان تالف (مصادرة مبلغ التأمين بالكامل)")
        self.radio_intact.setChecked(True)
        self.radio_intact.toggled.connect(self._calculate)
        cond_lay.addWidget(self.radio_intact)
        cond_lay.addWidget(self.radio_damaged)
        lay.addWidget(condition_group)
        
        self.result_lbl = QLabel()
        self.result_lbl.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #E0F2FE; border-radius: 5px;")
        self.result_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.result_lbl)
        
        from PyQt6.QtWidgets import QDialogButtonBox
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("تأكيد الإرجاع والتسوية")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        apply_button_style(btns.button(QDialogButtonBox.StandardButton.Ok), "primary")
        lay.addWidget(btns)
        
        self._calculate()

    def _calculate(self):
        if self.radio_intact.isChecked():
            final_total = self.rental_price
        else:
            final_total = self.total_amount
            
        diff = self.paid - final_total
        if diff > 0:
            self.final_refund = diff
            self.final_collection = 0
            self.result_lbl.setText(f"يجب رد مبلغ للعميل قدره: {diff} جنيه")
            self.result_lbl.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #FEF08A; color: #854D0E;")
        elif diff < 0:
            self.final_refund = 0
            self.final_collection = abs(diff)
            self.result_lbl.setText(f"المبلغ المتبقي المطلوب تحصيله: {abs(diff)} جنيه")
            self.result_lbl.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #FECACA; color: #991B1B;")
        else:
            self.final_refund = 0
            self.final_collection = 0
            self.result_lbl.setText("الحساب خالص. لا يوجد متبقي أو مسترد.")
            self.result_lbl.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #D1FAE5; color: #065F46;")


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
        
        self.insurance = QDoubleSpinBox()
        self.insurance.setMaximum(100000)
        self.insurance.setDecimals(2)
        self.insurance.setValue(0.0)

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
        form.addRow("التأمين (جنيه):", self.insurance)
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
        insurance_val = self.insurance.value()
        rental_val = float(self.dress.get('rental_price', 0) or 0)
        total = rental_val + insurance_val
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
            rental_price=rental_val, deposit=insurance_val, discount=0, total_amount=total, paid_amount=paid,
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
            'rental_price': rental_val,
            'deposit': insurance_val,
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
        title_font.setPointSize(14)
        painter.setFont(title_font)
        painter.setPen(QColor("#1E293B"))
        total = sum(self.month_counts.values())
        painter.drawText(QRect(0, 20, w, 30), Qt.AlignmentFlag.AlignCenter, f"({total}) 📊 إحصائيات التأجير الشهرية")
        
        # إعداد البيانات
        months = sorted(self.month_counts.keys())
        counts = [self.month_counts[m] for m in months]
        max_count = max(counts) if counts else 0
        
        if not months or max_count == 0:
            no_data_font = painter.font()
            no_data_font.setPointSize(11)
            painter.setFont(no_data_font)
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "لا توجد بيانات")
            painter.end()
            return
        
        # حدود الرسم
        top_margin = 80
        bottom_margin = 60
        side_margin = 40
        chart_h = h - top_margin - bottom_margin
        chart_w = w - 2 * side_margin
        
        # حساب مواقع النقاط
        n = len(months)
        point_spacing = min(80, max(40, chart_w // n if n > 0 else 0))
        total_chart_width = n * point_spacing
        start_x = side_margin + (chart_w - total_chart_width) // 2 + (point_spacing // 2)
        
        base_y = h - bottom_margin
        
        points = []
        for i, month in enumerate(months):
            cnt = self.month_counts[month]
            height_ratio = cnt / max_count if max_count > 0 else 0
            point_h = int(chart_h * height_ratio)
            x = start_x + i * point_spacing
            y = base_y - point_h
            points.append((x, y, cnt, month))
            
        # رسم الخط المتصل والظل تحته
        if len(points) > 0:
            path = QPainterPath()
            path.moveTo(points[0][0], base_y)
            for pt in points:
                path.lineTo(pt[0], pt[1])
            path.lineTo(points[-1][0], base_y)
            path.closeSubpath()
            
            grad = QLinearGradient(0, top_margin, 0, base_y)
            grad.setColorAt(0.0, QColor(59, 130, 246, 100)) # أزرق شفاف
            grad.setColorAt(1.0, QColor(59, 130, 246, 10))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(path)
            
            # رسم الخط الأساسي (السهم)
            line_path = QPainterPath()
            line_path.moveTo(points[0][0], points[0][1])
            for pt in points[1:]:
                line_path.lineTo(pt[0], pt[1])
            
            pen = QPen(QColor("#3B82F6"), 2) # خط أزرق
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(line_path)
            
        # رسم الدوائر والنصوص فوق النقاط
        for x, y, cnt, month in points:
            painter.setPen(QPen(QColor("#1D4ED8"), 2))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(QPointF(x, y), 3, 3)
            
            if cnt > 0:
                label_font = painter.font()
                label_font.setBold(True)
                label_font.setPointSize(9)
                painter.setFont(label_font)
                painter.setPen(QColor("#1E293B"))
                painter.drawText(QRect(int(x - 20), int(y - 25), 40, 20), Qt.AlignmentFlag.AlignCenter, str(cnt))
            
            # اسم الشهر والسنة
            month_num = month[5:7] if len(month) >= 7 else month[5:]
            month_name = self.MONTH_NAMES.get(month_num, month_num)
            label_font.setBold(False)
            label_font.setPointSize(8)
            painter.setFont(label_font)
            painter.setPen(QColor("#64748B"))
            painter.drawText(QRect(int(x) - 30, base_y + 10, 60, 18), Qt.AlignmentFlag.AlignCenter, month_name)
            year = month[:4]
            painter.drawText(QRect(int(x) - 30, base_y + 25, 60, 16), Qt.AlignmentFlag.AlignCenter, year)
        
        painter.setPen(QPen(QColor("#CBD5E1"), 2))
        painter.drawLine(side_margin, base_y, w - side_margin, base_y)
        painter.end()


class DailyRentalChartWidget(QWidget):
    """رسم بياني يوضح عدد التأجيرات اليومية (آخر 30 يوم)."""
    
    def __init__(self, daily_counts: dict):
        super().__init__()
        self.daily_counts = daily_counts

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
        title_font.setPointSize(14)
        painter.setFont(title_font)
        painter.setPen(QColor("#1E293B"))
        total = sum(self.daily_counts.values())
        painter.drawText(QRect(0, 20, w, 30), Qt.AlignmentFlag.AlignCenter, f"({total}) 📊 إحصائيات التأجير اليومية")
        
        # إعداد البيانات
        days = sorted(self.daily_counts.keys())
        counts = [self.daily_counts[d] for d in days]
        max_count = max(counts) if counts else 0
        
        if not days or max_count == 0:
            no_data_font = painter.font()
            no_data_font.setPointSize(11)
            painter.setFont(no_data_font)
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "لا توجد بيانات")
            painter.end()
            return
        
        # حدود الرسم
        top_margin = 80
        bottom_margin = 60
        side_margin = 40
        chart_h = h - top_margin - bottom_margin
        chart_w = w - 2 * side_margin
        
        n = len(days)
        point_spacing = min(80, max(20, chart_w // n if n > 0 else 0))
        total_chart_width = (n - 1) * point_spacing
        start_x = side_margin + (chart_w - total_chart_width) // 2
        
        base_y = h - bottom_margin
        
        points = []
        for i, day in enumerate(days):
            cnt = self.daily_counts[day]
            height_ratio = cnt / max_count if max_count > 0 else 0
            point_h = int(chart_h * height_ratio)
            x = start_x + i * point_spacing
            y = base_y - point_h
            points.append((x, y, cnt, day))
            
        if len(points) > 0:
            path = QPainterPath()
            path.moveTo(points[0][0], base_y)
            for pt in points:
                path.lineTo(pt[0], pt[1])
            path.lineTo(points[-1][0], base_y)
            path.closeSubpath()
            
            grad = QLinearGradient(0, top_margin, 0, base_y)
            grad.setColorAt(0.0, QColor(16, 185, 129, 100))
            grad.setColorAt(1.0, QColor(16, 185, 129, 10))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(path)
            
            line_path = QPainterPath()
            line_path.moveTo(points[0][0], points[0][1])
            for pt in points[1:]:
                line_path.lineTo(pt[0], pt[1])
            
            pen = QPen(QColor("#10B981"), 2)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(line_path)
            
        for i, (x, y, cnt, day) in enumerate(points):
            painter.setPen(QPen(QColor("#047857"), 2))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(QPointF(x, y), 3, 3)
            
            if cnt > 0:
                label_font = painter.font()
                label_font.setBold(True)
                label_font.setPointSize(9)
                painter.setFont(label_font)
                painter.setPen(QColor("#1E293B"))
                painter.drawText(QRect(int(x - 20), int(y - 25), 40, 20), Qt.AlignmentFlag.AlignCenter, str(cnt))
            
            # Show date labels
            skip = max(1, n // 10)
            if i % skip == 0 or i == n - 1 or cnt > 0:
                label_font.setBold(False)
                label_font.setPointSize(8)
                painter.setFont(label_font)
                painter.setPen(QColor("#64748B"))
                day_part = day[5:] # MM-DD
                painter.drawText(QRect(int(x) - 30, base_y + 10, 60, 18), Qt.AlignmentFlag.AlignCenter, day_part)
        
        painter.setPen(QPen(QColor("#CBD5E1"), 2))
        painter.drawLine(side_margin, base_y, w - side_margin, base_y)
        painter.end()


class DressDetailsWidget(QWidget):
    def __init__(self, db, back_callback, view_stats_callback):
        super().__init__()
        self.db = db
        self.back_callback = back_callback
        self.view_stats_callback = view_stats_callback
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
        content_lay.setSpacing(20)
        
        # Right: Image
        self.img_lbl = QLabel()
        self.img_lbl.setFixedSize(300, 400)
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_lbl.setStyleSheet("background:#FFF; border:2px dashed #CBD5E1; border-radius:10px;")
        content_lay.addWidget(self.img_lbl)
        
        # Middle: Details, Table & Buttons
        middle_lay = QVBoxLayout()
        self.title_lbl = QLabel()
        self.title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E293B;")
        middle_lay.addWidget(self.title_lbl)
        
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet("font-size: 16px; color: #475569;")
        middle_lay.addWidget(self.info_lbl)
        
        middle_lay.addSpacing(10)
        
        # Rentals Table
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        self.rentals_table = QTableWidget(0, 4)
        self.rentals_table.setHorizontalHeaderLabels(["العميل", "الاستلام", "الإرجاع", "إجراء"])
        self.rentals_table.horizontalHeader().setStretchLastSection(False)
        self.rentals_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.rentals_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.rentals_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.rentals_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.rentals_table.setColumnWidth(3, 330)
        self.rentals_table.setAlternatingRowColors(True)
        self.rentals_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.rentals_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rentals_table.verticalHeader().setVisible(False)
        self.rentals_table.verticalHeader().setDefaultSectionSize(65)
        self.rentals_table.setMinimumHeight(250)
        middle_lay.addWidget(self.rentals_table)

        middle_lay.addSpacing(10)
        
        # حالة الحجز
        self.status_lbl = QLabel()
        self.status_lbl.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px 16px; border-radius: 8px;")
        middle_lay.addWidget(self.status_lbl)
        
        middle_lay.addSpacing(10)
        
        # Buttons
        btns = QHBoxLayout()
        self.action_btn = QPushButton("➕ تأجير / حجز جديد")
        apply_button_style(self.action_btn, "primary")
        self.action_btn.setFixedHeight(50)
        self.action_btn.clicked.connect(self._on_main_action)
        btns.addWidget(self.action_btn, stretch=1)
        middle_lay.addLayout(btns)
        
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
        middle_lay.addLayout(mgmt_btns)
        
        middle_lay.addSpacing(10)
        self.stats_btn = QPushButton("📊 عرض إحصائيات التأجير")
        self.stats_btn.setStyleSheet("background-color: #8B5CF6; color: white; border-radius: 8px; font-weight: bold;")
        self.stats_btn.setFixedHeight(45)
        self.stats_btn.clicked.connect(lambda: self.view_stats_callback(self.dress['id']) if self.dress else None)
        middle_lay.addWidget(self.stats_btn)
        
        middle_lay.addStretch()
        content_lay.addLayout(middle_lay, stretch=2)

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
        self.info_lbl.setText(info)
        
        # Load active rentals
        active_rentals = self.db.conn.execute(
            "SELECT r.*, c.name as customer_name, c.phone as customer_phone, reg.name as registrar_name "
            "FROM rentals r JOIN customers c ON r.customer_id=c.id "
            "LEFT JOIN registrars reg ON r.registered_by_id=reg.id "
            "WHERE r.dress_id=? AND r.status='active' ORDER BY r.rental_date ASC",
            (self.dress['id'],)
        ).fetchall()
        
        from PyQt6.QtWidgets import QTableWidgetItem, QWidget, QHBoxLayout
        self.rentals_table.setRowCount(0)
        
        if active_rentals:
            self.status_lbl.setText(f"📛 محجوز (يوجد {len(active_rentals)} عملية نشطة)")
            self.status_lbl.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px 16px; border-radius: 8px; background: #FEE2E2; color: #DC2626;")
            
            for i, r in enumerate(active_rentals):
                self.rentals_table.insertRow(i)
                
                c_name = QTableWidgetItem(r['customer_name'])
                c_name.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.rentals_table.setItem(i, 0, c_name)
                
                r_date = QTableWidgetItem(r['rental_date'])
                r_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.rentals_table.setItem(i, 1, r_date)
                
                ret_date = QTableWidgetItem(r['expected_return_date'])
                ret_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.rentals_table.setItem(i, 2, ret_date)
                
                # Actions widget
                w = QWidget()
                w_lay = QHBoxLayout(w)
                w_lay.setContentsMargins(10, 10, 10, 10)
                w_lay.setSpacing(12)
                
                from PyQt6.QtWidgets import QSizePolicy
                ret_btn = QPushButton("↩ إرجاع")
                ret_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                ret_btn.setStyleSheet("background-color: #F59E0B; color: white; border-radius: 6px; font-weight: bold; font-size: 14px; padding: 4px 10px;")
                ret_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                ret_btn.clicked.connect(lambda checked, rid=r['id']: self._on_return_rental(rid))
                
                prt_btn = QPushButton("🖨 طباعة")
                prt_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                prt_btn.setStyleSheet("background-color: #3B82F6; color: white; border-radius: 6px; font-weight: bold; font-size: 14px; padding: 4px 10px;")
                prt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                # Convert sqlite3.Row to dict for printing
                r_dict = dict(r)
                prt_btn.clicked.connect(lambda checked, data=r_dict: self._print_specific_rental(data))
                
                cancel_btn = QPushButton("❌ إلغاء")
                cancel_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                cancel_btn.setStyleSheet("background-color: #EF4444; color: white; border-radius: 6px; font-weight: bold; font-size: 14px; padding: 4px 10px;")
                cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                cancel_btn.clicked.connect(lambda checked, rid=r['id']: self._on_cancel_rental(rid))
                
                w_lay.addWidget(cancel_btn)
                w_lay.addWidget(prt_btn)
                w_lay.addWidget(ret_btn)
                
                self.rentals_table.setCellWidget(i, 3, w)
                self.rentals_table.setRowHeight(i, 65)
        else:
            self.status_lbl.setText("✅ متاح للحجز")
            self.status_lbl.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px 16px; border-radius: 8px; background: #D1FAE5; color: #059669;")
        
        full_img = resolve_image_path(self.dress['image_path'])
        if full_img:
            pix = QPixmap(full_img)
            self.img_lbl.setPixmap(pix.scaled(self.img_lbl.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.img_lbl.setText("لا توجد صورة")
            self.img_lbl.setPixmap(QPixmap())
            
        # تم نقل الرسم البياني إلى صفحة DressStatisticsWidget

    def _on_main_action(self):
        # تأجير الفستان بغض النظر عن حالته
        dlg = SimpleRentalDialog(self, self.db, self.dress)
        if dlg.exec():
            inv = SimpleInvoiceDialog(self, dlg.rental_data)
            inv.exec()
            self.set_dress(self.dress['id'])

    def _on_return_rental(self, rental_id):
        rental = self.db.get_rental(rental_id)
        if not rental: return
        
        dlg = ReturnSettlementDialog(self, self.db, rental)
        if dlg.exec():
            actual_date = QDate.currentDate().toString("yyyy-MM-dd")
            
            # If intact, waive the deposit
            if dlg.radio_intact.isChecked() and rental['deposit'] > 0:
                new_total = float(rental['rental_price'])
                self.db.conn.execute("UPDATE rentals SET deposit=0, total_amount=?, remaining_amount=max(0, ?-paid_amount) WHERE id=?", 
                                     (new_total, new_total, rental_id))
                self.db.conn.commit()
            
            # Handle collection
            if dlg.final_collection > 0:
                self.db.return_dress(rental_id, actual_date, additional_payment=dlg.final_collection)
            else:
                self.db.return_dress(rental_id, actual_date)
                
            # Handle refund
            if dlg.final_refund > 0:
                self.db.add_refund(rental_id, dlg.final_refund, 'cash', 'استرداد مبلغ التأمين عند الإرجاع (الفستان سليم)')
                
            QMessageBox.information(self, "نجاح", "تم إرجاع الفستان وتسوية الحساب بنجاح.")
            self.set_dress(self.dress['id'])

    def _on_cancel_rental(self, rental_id):
        reply = QMessageBox.question(
            self, "إلغاء الحجز",
            "هل أنت متأكد من إلغاء هذا الحجز؟ سيتم إرجاع أي مبالغ مدفوعة للعميل وتسجيلها كاسترداد مالي.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            rental_dict = dict(self.db.get_rental(rental_id))
            self.db.cancel_rental(rental_id)
            
            # Notify owner
            try:
                from ui.owner_notify import notify_owner_action
                notify_owner_action(
                    db=self.db,
                    action_type='إلغاء حجز',
                    record=rental_dict
                )
            except Exception as e:
                print("WhatsApp error:", e)
                
            QMessageBox.information(self, "نجاح", "تم إلغاء الحجز بنجاح.")
            self.set_dress(self.dress['id'])

    def _print_specific_rental(self, rental_dict):
        data = {
            'id': rental_dict['id'],
            'customer_name': rental_dict['customer_name'],
            'customer_phone': rental_dict['customer_phone'],
            'dress_name': self.dress['name'],
            'dress_code': self.dress['code'],
            'dress_color': self.dress['color'],
            'dress_size': self.dress['size'],
            'rental_date': rental_dict['rental_date'],
            'return_date': rental_dict['expected_return_date'],
            'total_amount': rental_dict['total_amount'] or 0,
            'paid_amount': rental_dict['paid_amount'] or 0,
            'remaining_amount': rental_dict['remaining_amount'] or 0,
            'registrar_name': rental_dict['registrar_name'] or 'غير محدد',
            'deposit': rental_dict['deposit'] or 0
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
                    QMessageBox.warning(self, "خطأ", err or "لا يمكن حذف الفستان.")

class DressStatisticsWidget(QWidget):
    def __init__(self, db, back_callback):
        super().__init__()
        self.db = db
        self.back_callback = back_callback
        self.dress = None
        self._build_ui()

    def _build_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(20, 20, 20, 20)
        
        # شريط العودة والعنوان
        hdr = QHBoxLayout()
        self.back_btn = QPushButton("◀ عودة للتفاصيل")
        apply_button_style(self.back_btn, "secondary")
        self.back_btn.setFixedHeight(45)
        self.back_btn.clicked.connect(self.back_callback)
        hdr.addWidget(self.back_btn)
        
        self.title_lbl = QLabel("إحصائيات الفستان")
        self.title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E293B;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.addWidget(self.title_lbl, stretch=1)
        
        # spacer للموازنة
        spacer = QWidget()
        spacer.setFixedWidth(self.back_btn.width() if self.back_btn.width() > 0 else 150)
        hdr.addWidget(spacer)
        
        main_lay.addLayout(hdr)
        main_lay.addSpacing(20)
        
        self.chart_container = QVBoxLayout()
        main_lay.addLayout(self.chart_container, stretch=1)

    def set_dress(self, dress_id):
        dress_row = self.db.get_dress(dress_id)
        if not dress_row: return
        self.dress = dict(dress_row)
        self.title_lbl.setText(f"إحصائيات {self.dress['name']} (كود: {self.dress['code']})")
        
        for i in reversed(range(self.chart_container.count())): 
            w = self.chart_container.itemAt(i).widget()
            if w: w.deleteLater()
            
        # البيانات اليومية
        daily_rows = self.db.conn.execute(
            "SELECT strftime('%Y-%m-%d', rental_date) as day, COUNT(*) as cnt FROM rentals WHERE dress_id=? GROUP BY day ORDER BY day DESC LIMIT 60",
            (dress_id,)
        ).fetchall()
        daily_counts = {row['day']: row['cnt'] for row in daily_rows}
        
        # البيانات الشهرية
        monthly_rows = self.db.conn.execute(
            "SELECT strftime('%Y-%m', rental_date) as month, COUNT(*) as cnt FROM rentals WHERE dress_id=? GROUP BY month ORDER BY month DESC LIMIT 12",
            (dress_id,)
        ).fetchall()
        monthly_counts = {row['month']: row['cnt'] for row in monthly_rows}
        
        # تم إزالة بيانات الاختبار الوهمية
        
        # إنشاء وعرض الرسوم
        daily_chart = DailyRentalChartWidget(daily_counts)
        monthly_chart = MonthlyRentalChartWidget(monthly_counts)
        
        # جعل كل رسم يأخذ نفس المساحة
        self.chart_container.addWidget(daily_chart, stretch=1)
        self.chart_container.addSpacing(10)
        self.chart_container.addWidget(monthly_chart, stretch=1)

class CashierGridWidget(QWidget):
    def __init__(self, db, select_callback, back_to_dashboard_callback):
        super().__init__()
        self.db = db
        self.select_callback = select_callback
        self.back_to_dashboard_callback = back_to_dashboard_callback
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        
        # Header actions
        actions_lay = QHBoxLayout()
        
        # Back to Dashboard Button
        self.back_btn = QPushButton("◀ عودة للرئيسية")
        apply_button_style(self.back_btn, "secondary")
        self.back_btn.setFixedHeight(45)
        self.back_btn.clicked.connect(self.back_to_dashboard_callback)
        actions_lay.addWidget(self.back_btn)
        
        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 بحث باسم الفستان أو الكود...")
        self.search.setStyleSheet("padding: 10px; font-size: 16px; border-radius: 8px; border: 1px solid #CBD5E1;")
        self.search.textChanged.connect(lambda text: self._reload_with_current_filter())
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
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.setGridSize(QSize(180, 260))
        self.list_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
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

    def load_data(self, status_filter=None):
        self.current_status_filter = status_filter
        self._reload_with_current_filter()

    def _reload_with_current_filter(self):
        self.list_widget.clear()
        search = self.search.text().strip() or None
        
        dresses = self.db.get_all_dresses(search=search)
        
        if hasattr(self, 'current_status_filter') and self.current_status_filter:
            dresses = [d for d in dresses if d['status'] == self.current_status_filter]
        
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
    def __init__(self, db, back_to_dashboard_callback):
        super().__init__()
        self.db = db
        self.back_to_dashboard_callback = back_to_dashboard_callback
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)
        
        self.grid_view = CashierGridWidget(self.db, self._show_details, self.back_to_dashboard_callback)
        self.details_view = DressDetailsWidget(self.db, self._show_grid, self._show_stats)
        self.stats_view = DressStatisticsWidget(self.db, self._hide_stats)
        
        self.stack.addWidget(self.grid_view)
        self.stack.addWidget(self.details_view)
        self.stack.addWidget(self.stats_view)

    def _show_details(self, dress_id):
        self.details_view.set_dress(dress_id)
        self.stack.setCurrentIndex(1)

    def _show_stats(self, dress_id):
        self.stats_view.set_dress(dress_id)
        self.stack.setCurrentIndex(2)

    def _hide_stats(self):
        self.stack.setCurrentIndex(1)

    def _show_grid(self):
        self.grid_view._reload_with_current_filter()
        self.stack.setCurrentIndex(0)

    def load_dresses(self, status_filter=None):
        self.stack.setCurrentIndex(0)
        self.grid_view.load_data(status_filter)
