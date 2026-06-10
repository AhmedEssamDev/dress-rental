from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QLabel, QPushButton, QStackedWidget, QFrame, QSizePolicy,
                             QScrollArea)
from PyQt6.QtCore import Qt, QTimer, QEasingCurve, QPropertyAnimation
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from datetime import datetime


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("نظام تأجير الفساتين")
        self.setMinimumSize(1200, 750)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._build_ui()
        self._setup_clock()
        self.nav_buttons[0].setChecked(True)
        self._page_fade_anim = None

        QTimer.singleShot(1000, self._check_upcoming_alerts)

    def _check_upcoming_alerts(self):
        # Check for bookings happening within 1 day (today or tomorrow)
        near_bookings = self.db.get_upcoming_bookings(1)
        if near_bookings:
            from PyQt6.QtWidgets import QMessageBox, QApplication
            count = len(near_bookings)
            msg = f"🚨 إنذار هام: لديك {count} حجز (فساتين) يجب تسليمها غداً أو اليوم!\nيرجى مراجعة صفحة الحجوزات أو لوحة التحكم للتفاصيل."
            
            QApplication.beep()
            try:
                import winsound
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
            except:
                pass
            
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Critical)
            box.setWindowTitle("إنذار تسليم الفساتين")
            box.setText(msg)
            box.setStyleSheet("QLabel { font-size: 15px; font-weight: bold; color: #D32F2F; }")
            box.exec()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QHBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Sidebar ──
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(232)
        sidebar_lay = QVBoxLayout(sidebar)
        sidebar_lay.setContentsMargins(0, 0, 0, 0)
        sidebar_lay.setSpacing(0)

        # Logo area
        logo_frame = QFrame()
        logo_frame.setObjectName("sidebar_logo_frame")
        logo_lay = QVBoxLayout(logo_frame)
        logo_lay.setContentsMargins(15, 20, 15, 15)

        logo_icon = QLabel("👗")
        logo_icon.setObjectName("sidebar_logo_icon")
        logo_icon.setFont(QFont("Segoe UI Emoji", 30))
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        shop_name = QLabel("محل تأجير الفساتين")
        shop_name.setObjectName("sidebar_shop_name")
        shop_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.clock_lbl = QLabel("")
        self.clock_lbl.setObjectName("sidebar_clock")
        self.clock_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_lay.addWidget(logo_icon)
        logo_lay.addWidget(shop_name)
        logo_lay.addWidget(self.clock_lbl)
        sidebar_lay.addWidget(logo_frame)

        # Separator
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet("background:#3E3632;")
        sidebar_lay.addWidget(sep)

        # Nav buttons
        nav_items = [
            ("🏠", "لوحة التحكم", 0),
            ("👗", "الفساتين", 1),
            ("👥", "العملاء", 2),
            ("📅", "الحجوزات", 3),
            ("🧑‍💼", "المسجّلون", 4),
            ("📦", "التأجيرات", 5),
            ("📊", "التقارير", 6),
        ]

        self.nav_buttons = []
        for icon, label, idx in nav_items:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setFixedHeight(52)
            btn.setFont(QFont("Segoe UI", 12))
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            sidebar_lay.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_lay.addStretch()

        # Bottom info
        bottom = QLabel("نسخة 1.0\nجميع الحقوق محفوظة")
        bottom.setObjectName("sidebar_bottom_info")
        bottom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_lay.addWidget(bottom)

        main_lay.addWidget(sidebar)

        # ── Content area ──
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #F7F4F0;")
        main_lay.addWidget(self.stack)

        # Create pages
        from ui.dashboard import DashboardWidget
        from ui.dresses import DressesWidget
        from ui.customers import CustomersWidget
        from ui.bookings import BookingsWidget
        from ui.registrars import RegistrarsWidget
        from ui.rentals import RentalsWidget
        from ui.reports import ReportsWidget

        self.dashboard = DashboardWidget(db=self.db, switch_fn=self._switch_page)
        self.dresses = DressesWidget(db=self.db)
        self.customers = CustomersWidget(db=self.db)
        self.bookings = BookingsWidget(db=self.db)
        self.registrars = RegistrarsWidget(db=self.db)
        self.rentals = RentalsWidget(db=self.db)
        self.reports = ReportsWidget(db=self.db)

        self.stack.addWidget(self._wrap_page(self.dashboard))
        self.stack.addWidget(self._wrap_page(self.dresses))
        self.stack.addWidget(self._wrap_page(self.customers))
        self.stack.addWidget(self._wrap_page(self.bookings))
        self.stack.addWidget(self._wrap_page(self.registrars))
        self.stack.addWidget(self._wrap_page(self.rentals))
        self.stack.addWidget(self._wrap_page(self.reports))

    def _wrap_page(self, page_widget):
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        area.setWidget(page_widget)
        return area

    def _switch_page(self, index):
        self.stack.setCurrentIndex(index)
        
        # Update sidebar button state to match current page
        if 0 <= index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)
            
        self._animate_page_change()
        # Refresh data when switching
        if index == 0: self.dashboard.refresh()
        elif index == 1: self.dresses.load_data()
        elif index == 2: self.customers.load_data()
        elif index == 3: self.bookings.load_data()
        elif index == 4: self.registrars.load_data()
        elif index == 5: self.rentals.load_data()
        elif index == 6: self.reports.load_data()

    def _animate_page_change(self):
        page = self.stack.currentWidget()
        if not page:
            return
        effect = page.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(page)
            page.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._page_fade_anim = anim

    def _setup_clock(self):
        def update():
            now = datetime.now()
            days_ar = ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
            day = days_ar[now.weekday()]
            self.clock_lbl.setText(f"{day}\n{now.strftime('%Y-%m-%d  %H:%M:%S')}")
        update()
        timer = QTimer(self)
        timer.timeout.connect(update)
        timer.start(1000)

    def closeEvent(self, event):
        try:
            import os
            import shutil
            from datetime import datetime
            
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")
            
            db_path = getattr(self.db, 'db_path', 'dress_rental.db')
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_file)
                
                # Cleanup old backups (keep last 10)
                backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith(".db")], key=os.path.getmtime)
                while len(backups) > 10:
                    oldest = backups.pop(0)
                    try: os.remove(oldest)
                    except: pass
                    
        except Exception as e:
            print(f"Auto-backup failed: {e}")
            
        event.accept()
