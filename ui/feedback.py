"""تغذية بصرية موحّدة بعد الحفظ والتعديل."""

from PyQt6.QtWidgets import QMessageBox, QTableWidget


def notify_success(parent, message, title="تم بنجاح ✅"):
    QMessageBox.information(parent, title, message)


def focus_table_row(table: QTableWidget, row: int):
    if row < 0 or row >= table.rowCount():
        return
    table.selectRow(row)
    item = table.item(row, 0)
    if item:
        table.scrollToItem(item, QTableWidget.ScrollHint.PositionAtCenter)


def after_save(parent, table: QTableWidget, row: int, message: str):
    """رسالة نجاح + إبراز الصف المحدّث في الجدول."""
    notify_success(parent, message)
    focus_table_row(table, row)
