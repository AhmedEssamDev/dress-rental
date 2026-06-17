from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QGridLayout)
from PyQt6.QtCore import Qt
from styles import apply_button_style
import datetime

class RevenueCard(QFrame):
    def __init__(self, title, amount, color):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 12px;
                border: 2px solid {color};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 18px; color: #475569; font-weight: bold; border: none;")
        t_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t_lbl)
        
        a_lbl = QLabel(f"{amount:,.0f} ج")
        a_lbl.setStyleSheet(f"font-size: 32px; color: {color}; font-weight: bold; border: none;")
        a_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(a_lbl)

class RevenuesWidget(QWidget):
    def __init__(self, db, back_callback):
        super().__init__()
        self.db = db
        self.back_callback = back_callback
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(20)
        
        # Header
        hdr = QHBoxLayout()
        back_btn = QPushButton("◀ عودة للرئيسية")
        apply_button_style(back_btn, "secondary")
        back_btn.clicked.connect(self.back_callback)
        hdr.addWidget(back_btn)
        
        title = QLabel("إيرادات الخزينة")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E3A8A;")
        hdr.addStretch()
        hdr.addWidget(title)
        hdr.addStretch()
        lay.addLayout(hdr)
        
        # Cards Layout
        self.cards_lay = QHBoxLayout()
        lay.addLayout(self.cards_lay)
        
        lay.addSpacing(20)
        
        # Table for past 6 months
        subtitle = QLabel("إيرادات الأشهر السابقة")
        subtitle.setStyleSheet("font-size: 18px; font-weight: bold; color: #334155;")
        lay.addWidget(subtitle)
        
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["الشهر", "الإيرادات (جنيه)"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table)

    def load_data(self):
        for i in reversed(range(self.cards_lay.count())): 
            w = self.cards_lay.itemAt(i).widget()
            if w: w.deleteLater()
            
        stats = self.db.get_dashboard_stats()
        today_rev = stats.get('today_revenue', 0)
        monthly_rev = stats.get('monthly_revenue', 0)
        
        c1 = RevenueCard("إيرادات اليوم", today_rev, "#10B981")
        c2 = RevenueCard("إيرادات الشهر الحالي", monthly_rev, "#3B82F6")
        
        self.cards_lay.addWidget(c1)
        self.cards_lay.addWidget(c2)
        
        # Table data
        self.table.setRowCount(0)
        monthly_data = self.db.get_monthly_revenue(months=6)
        
        for i, row in enumerate(monthly_data):
            self.table.insertRow(i)
            self.table.setRowHeight(i, 50)
            
            # Format month string (e.g. 2026-06)
            month_str = row['month']
            total = row['total']
            
            item_m = QTableWidgetItem(month_str)
            item_m.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            item_t = QTableWidgetItem(f"{total:,.0f} ج")
            item_t.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.table.setItem(i, 0, item_m)
            self.table.setItem(i, 1, item_t)
