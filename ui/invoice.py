import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from datetime import datetime
from styles import apply_button_style


class InvoiceDialog(QDialog):
    def __init__(self, parent, db, rental):
        super().__init__(parent)
        self.db = db
        # تحويل sqlite3.Row إلى dict عادي حتى تعمل جميع استدعاءات .get()
        self.rental = dict(rental)
        self.setWindowTitle(f"فاتورة — رقم {self.rental['id']}")
        self.setMinimumSize(620, 780)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.setContentsMargins(15, 15, 15, 15)

        # ── شريط الأزرار ──
        btns = QHBoxLayout()
        btns.setSpacing(8)

        print_btn = QPushButton("🖨️  معاينة الفاتورة")
        apply_button_style(print_btn, "primary")
        print_btn.clicked.connect(lambda: self._print(mode="invoice"))
        
        direct_print_btn = QPushButton("🖨️ طباعة سريعة")
        apply_button_style(direct_print_btn, "success")
        direct_print_btn.clicked.connect(lambda: self._print_direct(mode="invoice"))

        receipt_btn = QPushButton("🧾  إيصال 80mm")
        apply_button_style(receipt_btn, "warning")
        receipt_btn.clicked.connect(lambda: self._print(mode="receipt"))

        whatsapp_btn = QPushButton("💬 إرسال واتساب")
        apply_button_style(whatsapp_btn, "success")
        whatsapp_btn.clicked.connect(self._send_whatsapp)

        pdf_btn = QPushButton("💾  حفظ PDF")
        apply_button_style(pdf_btn, "secondary")
        pdf_btn.clicked.connect(self._save_pdf)

        close_btn = QPushButton("إغلاق")
        apply_button_style(close_btn, "secondary")
        close_btn.clicked.connect(self.accept)

        btns.addWidget(print_btn)
        btns.addWidget(direct_print_btn)
        btns.addWidget(receipt_btn)
        btns.addWidget(whatsapp_btn)
        btns.addWidget(pdf_btn)
        btns.addStretch()
        btns.addWidget(close_btn)
        lay.addLayout(btns)

        # ── معاينة الفاتورة ──
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setHtml(self._generate_html())
        lay.addWidget(self.preview)

    # ──────────────────────────────────────────────
    #  توليد HTML
    # ──────────────────────────────────────────────
    def _generate_html(self):
        r = self.rental
        try:
            payments = self.db.get_rental_payments(r['id'])
        except Exception:
            payments = []

        payments_html = ""
        for p in payments:
            payments_html += f"""
            <tr dir="rtl">
                <td align="right">{p['payment_date'][:16] if p['payment_date'] else '—'}</td>
                <td align="right" style="font-weight:bold; color:#2563EB;">{(p['amount'] or 0):,.0f} ج</td>
                <td align="right">{'كاش' if p['payment_method']=='cash' else ('بطاقة' if p['payment_method']=='card' else 'تحويل')}</td>
                <td align="right" style="font-size:10pt;">{p['notes'] or '—'}</td>
            </tr>"""

        return f"""
        <html dir="rtl">
        <head>
        <meta charset="UTF-8">
        <style>
            body {{ 
                font-family: 'Arial', sans-serif; 
                direction: rtl; 
                text-align: right;
                margin: 15pt;
                font-size: 12pt;
                color: #1e293b;
            }}
            .header {{ 
                text-align: center; 
                border-bottom: 3pt solid #1E3A8A; 
                padding-bottom: 10pt; 
                margin-bottom: 20pt; 
            }}
            .section-title {{ 
                background: #f1f5f9;
                padding: 8pt 12pt;
                color: #1E3A8A;
                font-weight: bold;
                font-size: 14pt;
                border-right: 6pt solid #1E3A8A;
                margin-top: 20pt;
                margin-bottom: 10pt;
                text-align: right;
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse;
                direction: rtl;
            }}
            td {{ 
                padding: 8pt;
                font-size: 12pt;
                border-bottom: 1pt solid #e2e8f0;
                vertical-align: middle;
            }}
            .field-row {{
                display: block;
                margin-bottom: 5pt;
            }}
            .label {{ 
                font-weight: bold;
                color: #475569;
                display: inline-block;
                min-width: 80pt;
            }}
            .value {{ 
                display: inline-block;
                color: #000;
            }}
            .total-table {{
                width: 220pt;
                margin-right: 0;
                margin-left: auto;
                border: 2pt solid #1E3A8A;
                margin-top: 30pt;
            }}
            .total-label {{
                background: #f1f5f9;
                font-weight: bold;
                font-size: 13pt;
            }}
        </style>
        </head>
        <body align="right" dir="rtl">
            <div class="header">
                <h1 style="color:#1E3A8A; margin:0; font-size: 28pt;">👗 عماد جاد فاشون</h1>
                <h3 style="color:#64748B; margin:5pt 0;">فاتورة تأجير فساتين</h3>
                <p style="font-size:11pt; color:#94A3B8;">رقم الفاتورة: #{r['id']} | تاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>

            <div class="section-title" align="right">👤 بيانات العميل</div>
            <table align="right" dir="rtl">
                <tr>
                    <td align="right" style="width:50%;">
                        <span class="label">اسم العميل:</span>
                        <span class="value">{r['customer_name']}</span>
                    </td>
                    <td align="right" style="width:50%;">
                        <span class="label">رقم الهاتف:</span>
                        <span class="value">{r.get('customer_phone') or '—'}</span>
                    </td>
                </tr>
                <tr>
                    <td align="right" colspan="2">
                        <span class="label">العنوان:</span>
                        <span class="value">{r.get('address') or '—'}</span>
                    </td>
                </tr>
            </table>

            <div class="section-title" align="right">👗 بيانات الفستان</div>
            <table align="right" dir="rtl">
                <tr>
                    <td align="right" style="width:50%;">
                        <span class="label">كود الفستان:</span>
                        <span class="value">{r['dress_code']}</span>
                    </td>
                    <td align="right" style="width:50%;">
                        <span class="label">اسم الفستان:</span>
                        <span class="value">{r['dress_name']}</span>
                    </td>
                </tr>
                <tr>
                    <td align="right" style="width:50%;">
                        <span class="label">المقاس:</span>
                        <span class="value">{r.get('size') or '—'}</span>
                    </td>
                    <td align="right" style="width:50%;">
                        <span class="label">اللون:</span>
                        <span class="value">{r.get('color') or '—'}</span>
                    </td>
                </tr>
            </table>

            <div class="section-title" align="right">📅 تفاصيل التأجير</div>
            <table align="right" dir="rtl">
                <tr>
                    <td align="right" style="width:50%;">
                        <span class="label">تاريخ الاستلام:</span>
                        <span class="value">{r['rental_date']}</span>
                    </td>
                    <td align="right" style="width:50%;">
                        <span class="label">موعد الإرجاع:</span>
                        <span class="value">{r['expected_return_date']}</span>
                    </td>
                </tr>
                <tr>
                    <td align="right" style="width:50%;">
                        <span class="label">سعر الإيجار:</span>
                        <span class="value">{(r.get('rental_price') or 0):,.0f} ج</span>
                    </td>
                    <td align="right" style="width:50%;">
                        <span class="label">مبلغ التأمين:</span>
                        <span class="value">{(r.get('deposit') or 0):,.0f} ج</span>
                    </td>
                </tr>
            </table>

            {f'<div class="section-title" align="right">💰 سجل المدفوعات</div><table align="right" dir="rtl"><thead><tr style="background:#f8fafc;"><th align="right" style="padding:8pt;">التاريخ</th><th align="right" style="padding:8pt;">المبلغ</th><th align="right" style="padding:8pt;">الطريقة</th><th align="right" style="padding:8pt;">ملاحظات</th></tr></thead>{payments_html}</table>' if payments else ''}

            <table class="total-table" align="left" dir="rtl" style="margin-top:30pt;">
                <tr>
                    <td class="total-label" align="right">الإجمالي المطلوب:</td>
                    <td align="left" style="font-weight:bold; font-size:14pt;">{(r.get('total_amount') or 0):,.0f} ج</td>
                </tr>
                <tr>
                    <td class="total-label" align="right" style="color:#059669;">المبلغ المدفوع:</td>
                    <td align="left" style="color:#059669; font-weight:bold; font-size:14pt;">{(r.get('paid_amount') or 0):,.0f} ج</td>
                </tr>
                <tr style="background: #1E3A8A; color:white;">
                    <td align="right" style="font-weight:bold; font-size:16pt;">المبلغ المتبقي:</td>
                    <td align="left" style="font-weight:bold; font-size:16pt;">{(r.get('remaining_amount') or 0):,.0f} ج</td>
                </tr>
            </table>

            <div style="margin-top:100pt; text-align:center; border-top:1pt solid #cbd5e1; padding-top:15pt; color:#64748b; font-size:11pt;">
                شكراً لتعاملكم مع <b>عماد جاد فاشون</b> | يُرجى الالتزام بموعد الإرجاع
            </div>
        </body>
        </html>
        """

    # ──────────────────────────────────────────────
    #  توليد HTML للإيصال الحراري 80mm
    # ──────────────────────────────────────────────
    def _generate_receipt_html(self):
        r = self.rental
        return f"""
        <html dir="rtl">
        <head>
        <style>
            body {{ font-family: 'Arial'; width: 280pt; margin: 0; padding: 5pt; direction: rtl; text-align: right; }}
            .center {{ text-align: center; }}
            .line {{ border-top: 1pt dashed #000; margin: 5pt 0; }}
            table {{ width: 100%; border-collapse: collapse; direction: rtl; }}
            td {{ padding: 4pt 0; font-size: 12pt; }}
            .bold {{ font-weight: bold; }}
            .big {{ font-size: 16pt; }}
        </style>
        </head>
        <body align="right">
            <div class="center">
                <div class="big bold">عماد جاد فاشون</div>
                <div style="font-size: 11pt;">إيصال تأجير فساتين</div>
                <div style="font-size: 10pt;">رقم: #{r['id']} | {datetime.now().strftime('%Y-%m-%d')}</div>
            </div>
            <div class="line"></div>
            <table dir="rtl">
                <tr><td class="bold" width="30%">العميل:</td><td align="left">{r['customer_name']}</td></tr>
                <tr><td class="bold">الهاتف:</td><td align="left">{r.get('customer_phone') or '—'}</td></tr>
                <tr><td class="bold">الفستان:</td><td align="left">{r['dress_name']}</td></tr>
                <tr><td class="bold">الكود:</td><td align="left">{r['dress_code']}</td></tr>
                <tr><td class="bold">الاستلام:</td><td align="left">{r['rental_date']}</td></tr>
                <tr><td class="bold">الإرجاع:</td><td align="left">{r['expected_return_date']}</td></tr>
            </table>
            <div class="line"></div>
            <table dir="rtl">
                <tr><td>سعر الإيجار:</td><td align="left">{(r.get('rental_price') or 0):,.0f} ج</td></tr>
                <tr><td>التأمين:</td><td align="left">{(r.get('deposit') or 0):,.0f} ج</td></tr>
                <tr><td>المدفوع:</td><td align="left">{(r.get('paid_amount') or 0):,.0f} ج</td></tr>
                <tr class="big bold"><td>المتبقي:</td><td align="left">{(r.get('remaining_amount') or 0):,.0f} ج</td></tr>
            </table>
            <div class="line"></div>
            <div class="center bold" style="font-size: 12pt;">شكراً لزيارتكم!</div>
            <div class="center" style="font-size: 10pt;">يُرجى الاحتفاظ بالإيصال</div>
        </body>
        </html>
        """

    # ──────────────────────────────────────────────
    #  طباعة مباشرة عبر معاينة الطباعة أو بدونها
    # ──────────────────────────────────────────────
    def _print_direct(self, mode="invoice"):
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            if mode == "receipt":
                self._do_print_receipt(printer)
            else:
                self._do_print(printer)
            QMessageBox.information(self, "نجاح", "تم إرسال أمر الطباعة للطابعة الافتراضية بنجاح.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الطباعة", f"حدث خطأ أثناء الطباعة المباشرة:\n{e}")

    def _print(self, mode="invoice"):
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle("معاينة الطباعة")
            
            if mode == "receipt":
                preview.paintRequested.connect(self._do_print_receipt)
            else:
                preview.paintRequested.connect(self._do_print)
                
            preview.exec()
        except Exception as e:
            QMessageBox.critical(
                self, "خطأ في الطباعة",
                f"حدث خطأ أثناء محاولة الطباعة:\n{e}"
            )

    def _do_print(self, printer):
        doc = QTextDocument()
        doc.setHtml(self._generate_html())
        doc.print(printer)

    def _do_print_receipt(self, printer):
        doc = QTextDocument()
        doc.setHtml(self._generate_receipt_html())
        doc.print(printer)

    # ──────────────────────────────────────────────
    #  إرسال عبر الواتساب
    # ──────────────────────────────────────────────
    def _send_whatsapp(self):
        import webbrowser
        from urllib.parse import quote
        
        r = self.rental
        phone = r.get('customer_phone') or ""
        
        # تنظيف الرقم من المسافات والرموز
        phone = ''.join(filter(str.isdigit, phone))
        
        if not phone:
            QMessageBox.warning(self, "تنبيه", "لا يوجد رقم هاتف مسجل لهذا العميل لإرسال الرسالة.")
            return
            
        # إضافة مفتاح مصر إذا كان الرقم محلي
        if phone.startswith("01") and len(phone) == 11:
            phone = "+2" + phone
            
        msg = "👗 عماد جاد فاشون 👗\n\n"
        msg += f"مرحباً أ/ {r.get('customer_name')}\n"
        msg += "إليك تفاصيل الحجز الخاص بك:\n\n"
        msg += f"رقم الفاتورة: #{r.get('id')}\n"
        msg += f"الفستان: {r.get('dress_name')} ({r.get('dress_code')})\n"
        msg += f"تاريخ الاستلام: {r.get('rental_date')}\n"
        msg += f"موعد الإرجاع: {r.get('expected_return_date')}\n"
        msg += "-----------------\n"
        msg += f"الإجمالي المطلوب: {(r.get('total_amount') or 0):,.0f} ج\n"
        msg += f"المبلغ المدفوع: {(r.get('paid_amount') or 0):,.0f} ج\n"
        msg += f"المبلغ المتبقي: {(r.get('remaining_amount') or 0):,.0f} ج\n\n"
        msg += "شكراً لتعاملكم معنا، يُرجى الالتزام بموعد الإرجاع."

        # فتح رابط الواتساب عبر المتصفح
        url = f"https://api.whatsapp.com/send?phone={phone}&text={quote(msg)}"
        webbrowser.open(url)

    # ──────────────────────────────────────────────
    #  حفظ كـ PDF
    # ──────────────────────────────────────────────
    def _save_pdf(self):
        try:
            default_name = f"فاتورة_{self.rental['id']}.pdf"
            path, _ = QFileDialog.getSaveFileName(
                self, "حفظ الفاتورة كـ PDF",
                default_name,
                "PDF Files (*.pdf)"
            )
            if not path:
                return

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)

            doc = QTextDocument()
            doc.setHtml(self._generate_html())
            doc.print(printer)

            reply = QMessageBox.question(
                self, "✅ تم الحفظ بنجاح",
                f"تم حفظ الفاتورة في:\n{path}\n\nهل تريد فتحها الآن؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                os.startfile(path)

        except Exception as e:
            QMessageBox.critical(
                self, "خطأ في الحفظ",
                f"حدث خطأ أثناء حفظ الملف:\n{str(e)}"
            )
