from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit)
from PyQt6.QtCore import Qt
from styles import apply_button_style

class CustomersWidget(QWidget):
    def __init__(self, db, back_callback):
        super().__init__()
        self.db = db
        self.back_callback = back_callback
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(15)
        
        # Header
        hdr = QHBoxLayout()
        back_btn = QPushButton("◀ عودة للرئيسية")
        apply_button_style(back_btn, "secondary")
        back_btn.clicked.connect(self.back_callback)
        hdr.addWidget(back_btn)
        
        title = QLabel("قائمة العملاء")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E3A8A;")
        hdr.addStretch()
        hdr.addWidget(title)
        hdr.addStretch()
        lay.addLayout(hdr)
        
        # Search
        search_lay = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 بحث باسم العميل أو رقم الهاتف...")
        self.search.setStyleSheet("padding: 10px; font-size: 16px; border-radius: 8px; border: 1px solid #CBD5E1;")
        self.search.textChanged.connect(self.load_data)
        search_lay.addWidget(self.search)
        lay.addLayout(search_lay)
        
        # Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["م", "اسم العميل", "رقم الهاتف", "حذف"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        search = self.search.text().strip() or None
        customers = self.db.get_all_customers(search=search)
        
        from PyQt6.QtWidgets import QMessageBox
        
        for i, c in enumerate(customers):
            self.table.insertRow(i)
            self.table.setRowHeight(i, 50)
            
            vals = [str(i+1), c['name'], c['phone'] or 'لا يوجد']
            for col, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, col, item)
                
            del_btn = QPushButton("🗑️")
            del_btn.setStyleSheet("background-color: #EF4444; color: white; border-radius: 4px; padding: 4px;")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda checked, cid=c['id'], cname=c['name']: self._on_delete_customer(cid, cname))
            self.table.setCellWidget(i, 3, del_btn)

    def _on_delete_customer(self, cid, cname):
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                     f"هل أنت متأكد من حذف العميل «{cname}»؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            ok, err = self.db.delete_customer(cid)
            if ok:
                QMessageBox.information(self, "نجاح", "تم حذف العميل بنجاح.")
                self.load_data()
            else:
                QMessageBox.warning(self, "خطأ", err)
