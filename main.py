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

    # # Инициализация базы данных
    # init_db()

    # # Создаем сессию для работы с БД
    # session = SessionLocal()

    # # Передаем сессию в окно логина
    # login_dialog = LoginDialog(session)
    # print('open')

    # if login_dialog.exec() == QDialog.DialogCode.Accepted:
    #     window = MainWindow()
    #     window.show()
    #     app.exec()
    # else:
    #     choice = QMessageBox.question(None, "Ошибка", "Не удалось войти в систему. Хотите зарегистрироваться?", 
    #                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

    #     if choice == QMessageBox.StandardButton.Yes:
    #         register_dialog = RegisterDialog()

    #         if register_dialog.exec() == QDialog.DialogCode.Accepted:
    #             QMessageBox.information(None, "Успех", "Вы успешно зарегистрированы!")
    #             window = MainWindow()
    #             window.show()
    #             app.exec()
    #         else:
    #             QMessageBox.warning(None, "Ошибка", "Регистрация не удалась.")
    #     else:
    #         QMessageBox.warning(None, "Ошибка", "Не удалось войти в систему.")
