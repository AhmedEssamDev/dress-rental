from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGridLayout, QFrame)
from PyQt6.QtCore import Qt
from styles import apply_button_style

class DashboardCard(QFrame):
    def __init__(self, title, count, icon, color, callback):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 15px;
                border: 1px solid #E2E8F0;
            }}
            QFrame:hover {{
                border: 2px solid {color};
                background-color: #F8FAFC;
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mousePressEvent = lambda e: callback()
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        
        top_lay = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 32px; color: {color}; background: transparent; border: none;")
        top_lay.addWidget(icon_lbl)
        top_lay.addStretch()
        lay.addLayout(top_lay)
        
        count_lbl = QLabel(str(count))
        count_lbl.setStyleSheet(f"font-size: 36px; font-weight: bold; color: #1E293B; background: transparent; border: none;")
        lay.addWidget(count_lbl)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 18px; color: #64748B; background: transparent; border: none;")
        lay.addWidget(title_lbl)

class DashboardWidget(QWidget):
    def __init__(self, db, nav_callback):
        super().__init__()
        self.db = db
        self.nav_callback = nav_callback  # function to navigate to different views
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(30)
        
        # Header
        title = QLabel("لوحة التحكم (الرئيسية)")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E3A8A;")
        lay.addWidget(title)
        
        # Grid for cards
        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        lay.addLayout(self.grid)
        lay.addStretch()
        
    def load_data(self):
        # Clear grid
        for i in reversed(range(self.grid.count())): 
            w = self.grid.itemAt(i).widget()
            if w: w.deleteLater()
            
        stats = self.db.get_dashboard_stats()
        dresses_stats = stats.get('dresses', {})
        total_dresses = sum(dresses_stats.values())
        available_dresses = dresses_stats.get('available', 0)
        rented_dresses = dresses_stats.get('rented', 0)
        total_customers = stats.get('total_customers', 0)
        monthly_rev = stats.get('monthly_revenue', 0)
        
        # Cards
        c1 = DashboardCard("إجمالي الفساتين", total_dresses, "👗", "#3B82F6", lambda: self.nav_callback('dresses', None))
        c2 = DashboardCard("الفساتين المتاحة", available_dresses, "✅", "#10B981", lambda: self.nav_callback('dresses', 'available'))
        c3 = DashboardCard("الفساتين المأجرة", rented_dresses, "📛", "#EF4444", lambda: self.nav_callback('dresses', 'rented'))
        c4 = DashboardCard("العملاء", total_customers, "👥", "#8B5CF6", lambda: self.nav_callback('customers', None))
        c5 = DashboardCard("الإيرادات", "", "💰", "#F59E0B", lambda: self.nav_callback('revenues', None))
        
        self.grid.addWidget(c1, 0, 0)
        self.grid.addWidget(c2, 0, 1)
        self.grid.addWidget(c3, 0, 2)
        self.grid.addWidget(c4, 1, 0)
        self.grid.addWidget(c5, 1, 1)
