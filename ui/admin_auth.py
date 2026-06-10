from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox
from PyQt6.QtCore import Qt
from styles import style_dialog_buttons

class AdminAuthDialog(QDialog):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("تأكيد الصلاحية")
        self.setMinimumWidth(300)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        lay = QVBoxLayout(self)
        form = QFormLayout()
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("كلمة مرور المدير...")
        
        form.addRow("كلمة المرور:", self.password_input)
        lay.addLayout(form)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("تأكيد")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        btns.accepted.connect(self._verify)
        btns.rejected.connect(self.reject)
        style_dialog_buttons(btns)
        
        lay.addWidget(btns)

    def _verify(self):
        pwd = self.password_input.text()
        if self.db.verify_admin_password(pwd):
            self.accept()
        else:
            QMessageBox.warning(self, "خطأ", "كلمة المرور غير صحيحة.")
            self.password_input.clear()
            self.password_input.setFocus()
