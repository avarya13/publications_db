from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton
from services.user_service import create_user
from models.relational_models import Permissions

class AddUserDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавить пользователя")
        self.setGeometry(200, 200, 300, 200)

        layout = QVBoxLayout()

        # Поле для ввода имени пользователя
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Имя пользователя")
        layout.addWidget(QLabel("Имя пользователя:"))
        layout.addWidget(self.username_input)

        # Поле для ввода пароля
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_input)

        # Выпадающий список для выбора роли
        self.role_combo = QComboBox(self)
        self.role_combo.addItems([Permissions.FULL_ACCESS, Permissions.READ_ONLY, Permissions.COMBINED])
        layout.addWidget(QLabel("Роль:"))
        layout.addWidget(self.role_combo)

        # Кнопка для добавления пользователя
        self.add_button = QPushButton("Добавить", self)
        self.add_button.clicked.connect(self.add_user)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def add_user(self):
        username = self.username_input.text()
        password = self.password_input.text()
        role = self.role_combo.currentText()

        # Вызов функции для создания пользователя
        create_user(username, password, role)
        self.accept()

# if __name__ == "__main__":
#     import sys
#     from PyQt6.QtWidgets import QApplication

#     app = QApplication(sys.argv)  # Создание QApplication перед виджетами
#     dialog = AddUserDialog()
#     dialog.exec()  # Запускаем диалог
