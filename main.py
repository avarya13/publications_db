from gui.main_window import MainWindow
from gui.login import LoginDialog
from gui.register import RegisterDialog
from database.relational import init_db, SessionLocal
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()