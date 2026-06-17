from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QLabel, QFrame, QPushButton, QDialog,
                             QListWidget, QListWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon

from ui.cashier import CashierWidget
from ui.dashboard import DashboardWidget
from ui.customers import CustomersWidget
from ui.revenues import RevenuesWidget
import os

class NotificationsDialog(QDialog):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("🔔 إشعارات المناسبات القريبة")
        self.setMinimumSize(500, 400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; }
            QListWidget::item { border-bottom: 1px solid #E2E8F0; }
        """)
        lay.addWidget(self.list_widget)
        
        notifs = self.db.get_notifications()
        if not notifs:
            self.list_widget.addItem("لا توجد إشعارات حالية.")
        else:
            from datetime import date
            today = date.today().isoformat()
            for n in notifs:
                event_date = n['event_date']
                if event_date == today:
                    status = "🔴 اليوم"
                elif event_date > today:
                    status = f"🟡 القادم ({event_date})"
                else:
                    status = f"⚫ متأخر ({event_date})"
                if n.get('type') == 'booking':
                    kind = "تسليم (حجز)"
                elif n.get('type') == 'delivery':
                    kind = "تسليم (تأجير)"
                else:
                    kind = "إرجاع (تأجير)"
                txt = f"{status} - {kind} - {n['dress_name']} ({n['dress_code']})\nالعميل: {n['customer_name']} | رقم الهاتف: {n['customer_phone']}\nبواسطة: {n['registrar_name'] or 'غير محدد'}"
                
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, dict(n))
                
                w = QWidget()
                w_lay = QHBoxLayout(w)
                w_lay.setContentsMargins(5, 5, 5, 5)
                
                del_btn = QPushButton("🗑️")
                del_btn.setStyleSheet("background-color: transparent; border: none; font-size: 18px; color: #EF4444;")
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.clicked.connect(lambda checked, i=item: self._delete_item(i))
                
                lbl = QLabel(txt)
                lbl.setStyleSheet("font-size: 13px; color: #1E293B;")
                
                w_lay.addWidget(lbl)
                w_lay.addStretch()
                w_lay.addWidget(del_btn)
                
                item.setSizeHint(QSize(0, 80))
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, w)
                
        btns_lay = QHBoxLayout()
        btns_lay.addStretch()
        
        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet("background-color: #4A4543; color: white; padding: 8px; border-radius: 6px; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        btns_lay.addWidget(close_btn)
        
        lay.addLayout(btns_lay)

    def _delete_item(self, item):
        n = item.data(Qt.ItemDataRole.UserRole)
        self.db.dismiss_notification(n['type'], n['id'])
        
        row = self.list_widget.row(item)
        self.list_widget.takeItem(row)

class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("نظام الكاشير - تأجير الفساتين")
        self.setMinimumSize(1200, 750)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._build_ui()
        self._update_notifications()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #1E3A8A; color: white;")
        header.setFixedHeight(60)
        hdr_lay = QHBoxLayout(header)
        hdr_lay.setContentsMargins(20, 0, 20, 0)
        
        # Logo
        logo_lbl = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "logo.jpeg")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            logo_lbl.setPixmap(pix.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        hdr_lay.addWidget(logo_lbl)
        
        title = QLabel("نظام تأجير الفساتين - الكاشير")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        hdr_lay.addWidget(title)
        
        hdr_lay.addStretch()
        
        # Notifications Button
        self.notif_btn = QPushButton("🔔 الإشعارات")
        self.notif_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6; color: white; font-weight: bold; padding: 8px 15px;
                border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        self.notif_btn.clicked.connect(self._show_notifications)
        hdr_lay.addWidget(self.notif_btn)
        
        main_lay.addWidget(header)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #F7F4F0;")
        main_lay.addWidget(self.stack)

        self.dashboard = DashboardWidget(self.db, self._navigate)
        self.cashier = CashierWidget(self.db, self._show_dashboard)
        self.customers = CustomersWidget(self.db, self._show_dashboard)
        self.revenues = RevenuesWidget(self.db, self._show_dashboard)

        self.stack.addWidget(self.dashboard) # 0
        self.stack.addWidget(self.cashier)   # 1
        self.stack.addWidget(self.customers) # 2
        self.stack.addWidget(self.revenues)  # 3
        
        self._show_dashboard()

    def _show_dashboard(self):
        self.dashboard.load_data()
        self.stack.setCurrentIndex(0)
        
    def _navigate(self, page, param=None):
        if page == 'dresses':
            self.cashier.load_dresses(status_filter=param)
            self.stack.setCurrentIndex(1)
        elif page == 'customers':
            self.customers.load_data()
            self.stack.setCurrentIndex(2)
        elif page == 'revenues':
            self.revenues.load_data()
            self.stack.setCurrentIndex(3)

    def _update_notifications(self):
        notifs = self.db.get_notifications()
        count = len(notifs)
        if count > 0:
            self.notif_btn.setText(f"🔔 الإشعارات ({count})")
            self.notif_btn.setStyleSheet("""
                QPushButton {
                    background-color: #EF4444; color: white; font-weight: bold; padding: 8px 15px;
                    border-radius: 6px; border: none;
                }
                QPushButton:hover { background-color: #DC2626; }
            """)
        else:
            self.notif_btn.setText("🔔 الإشعارات")
            self.notif_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3B82F6; color: white; font-weight: bold; padding: 8px 15px;
                    border-radius: 6px; border: none;
                }
                QPushButton:hover { background-color: #2563EB; }
            """)

    def _show_notifications(self):
        dlg = NotificationsDialog(self, self.db)
        dlg.exec()
        self._update_notifications()

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
