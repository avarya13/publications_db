from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from werkzeug.security import check_password_hash
from models.relational_models import User

class LoginDialog(QDialog):
    def __init__(self, session):
        super().__init__()
        self.setWindowTitle("Вход")
        self.setGeometry(200, 200, 300, 200)

        self.session = session  

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

        # Кнопка для входа
        self.login_button = QPushButton("Войти", self)
        self.login_button.clicked.connect(self.login_user)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def login_user(self):
        username = self.username_input.text()
        password = self.password_input.text()

        # Поиск пользователя в базе данных
        user = self.session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            QMessageBox.information(self, "Успех", "Вы успешно вошли в систему!")
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверные имя пользователя или пароль.")
