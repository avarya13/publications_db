from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox
from werkzeug.security import check_password_hash
from models.relational_models import User, UserRole
from gui.register import RegisterDialog

class LoginDialog(QDialog):
    def __init__(self, session, session_manager):
        super().__init__()
        self.setWindowTitle("Вход")
        self.setGeometry(200, 200, 300, 300)  # Увеличиваем размер окна для галочки

        self.session = session
        self.session_manager = session_manager

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

        # Галочка для входа как гость
        self.guest_checkbox = QCheckBox("Войти как гость", self)
        layout.addWidget(self.guest_checkbox)

        # Кнопка для входа
        self.login_button = QPushButton("Войти", self)
        self.login_button.clicked.connect(self.login_user)
        layout.addWidget(self.login_button)

        # Кнопка для перехода к регистрации
        self.register_button = QPushButton("Зарегистрироваться", self)
        self.register_button.clicked.connect(self.open_register_dialog)
        layout.addWidget(self.register_button)

        self.setLayout(layout)

    def login_user(self):
        """Метод для входа пользователя в систему."""
        if self.guest_checkbox.isChecked():
            # Вход как гость
            guest_user = self.session.query(User).filter_by(username="guest").first()
            if not guest_user:
                guest_user = User(
                    username="guest",
                    password_hash="",  # Можно оставить пустым, не используется
                    role=UserRole.GUEST
                )
                self.session.add(guest_user)
                self.session.commit()

            self.session_manager.set_authenticated_user(guest_user.user_id)
            self.session_manager.set_user_role(UserRole.GUEST)
            QMessageBox.information(self, "Успех", "Вы вошли как гость.")
            self.accept()
        else:
            # Обычный вход по имени пользователя и паролю
            username = self.username_input.text()
            password = self.password_input.text()

            # Поиск пользователя в базе данных
            user = self.session.query(User).filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                QMessageBox.information(self, "Успех", "Вы успешно вошли в систему!")

                # Устанавливаем пользователя
                self.session_manager.set_authenticated_user(user.user_id)

                # Устанавливаем роль пользователя
                self.session_manager.set_user_role(user.role)

                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверные имя пользователя или пароль.")

    def open_register_dialog(self):
        """Открывает окно регистрации."""
        register_dialog = RegisterDialog(self.session, self.session_manager)
        if register_dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Успех", "Вы успешно зарегистрированы!")
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Регистрация не удалась.")

    def toggle_guest_checkbox(self):
        """Переключает галочку для входа как гость, если одно из полей заполнено."""
        if self.username_input.text() or self.password_input.text():
            self.guest_checkbox.setChecked(False)  # Отключаем галочку, если есть введенные данные
            self.guest_checkbox.setEnabled(False)  # Делаем галочку неактивной
        else:
            self.guest_checkbox.setEnabled(True)  # Включаем галочку, если поля пусты

    def on_username_changed(self):
        self.toggle_guest_checkbox()

    def on_password_changed(self):
        self.toggle_guest_checkbox()

    def showEvent(self, event):
        super().showEvent(event)
        # Привязка событий для полей ввода
        self.username_input.textChanged.connect(self.on_username_changed)
        self.password_input.textChanged.connect(self.on_password_changed)
