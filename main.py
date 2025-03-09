from gui.main_window import MainWindow
from gui.login import LoginDialog
from gui.register import RegisterDialog
from database.relational import init_db
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog

if __name__ == "__main__":
    # app = QApplication([])
    # window = MainWindow() #LoginDialog() #
    # window.show()
    # app.exec()

    app = QApplication([])  # Инициализация приложения
    init_db()  # Инициализация базы данных

    print('opening')

    # Показываем окно входа при старте
    login_dialog = LoginDialog()
    print('open')
    
    if login_dialog.exec() == QDialog.DialogCode.Accepted:

        print('app')
        window = MainWindow()  # Создание окна после успешного входа
        window.show()  # Отображение окна
        app.exec()  # Запуск цикла обработки событий
    else:
        # Если вход не удался, показываем сообщение
        choice = QMessageBox.question(None, "Ошибка", "Не удалось войти в систему. Хотите зарегистрироваться?", 
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if choice == QMessageBox.StandardButton.Yes:
            # Если пользователь нажал "Yes", открываем окно регистрации
            register_dialog = RegisterDialog()

            if register_dialog.exec() == QDialog.DialogCode.Accepted:
                # После успешной регистрации создаем главное окно
                QMessageBox.information(None, "Успех", "Вы успешно зарегистрированы!")
                
                # Переходим к основному окну
                window = MainWindow()
                window.show()  # Отображаем окно публикаций
                app.exec()  # Запускаем основной цикл приложения
            else:
                QMessageBox.warning(None, "Ошибка", "Регистрация не удалась.")
        else:
            QMessageBox.warning(None, "Ошибка", "Не удалось войти в систему.")