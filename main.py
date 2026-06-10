import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from database import Database
from ui.animations import install_global_animations
from ui.main_window import MainWindow
from styles import MAIN_STYLE


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("نظام تأجير الفساتين")
    app.setOrganizationName("DressRental")
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setStyleSheet(MAIN_STYLE)

    # Set default font
    font = QFont("Segoe UI", 12)
    app.setFont(font)

    # Initialize database
    db = Database()

    # Main window
    window = MainWindow(db)
    window.show()
    app._ui_animator = install_global_animations(app, window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
