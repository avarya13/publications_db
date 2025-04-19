from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox
from werkzeug.security import check_password_hash
from models.relational_models import User, UserRole
from gui.register import RegisterDialog

class LoginDialog(QDialog):
    def __init__(self, session, session_manager):
        super().__init__()
        self.setWindowTitle("Вход")
        self.setGeometry(200, 200, 350, 400)  # Размер окна для улучшения интерфейса

        self.session = session
        self.session_manager = session_manager

        layout = QVBoxLayout()

        # Поле для ввода имени пользователя
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Введите имя пользователя")
        layout.addWidget(QLabel("Имя пользователя:"))
        layout.addWidget(self.username_input)

        # Поле для ввода пароля
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Введите пароль")
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

        # Стиль

        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
                font-family: Segoe UI, sans-serif;
                background-color: #f9f7f3;
            }

            QLabel {
                margin-bottom: 2px;
                padding-top: 4px;
                font-size: 13px;
                color: #3b3b3b;
            }

            QLineEdit {
                padding: 6px;
                margin-bottom: 4px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }

            QPushButton {
                padding: 8px 16px;
                background-color: #e5e2d7;
                color: #4a4a4a;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
                margin-top: 8px;
            }

            QPushButton:hover:enabled {
                background-color: #d8d5c9;
                color: #333; 
            }

            QPushButton:disabled {
                background-color: #f0ede5;
                color: #a0a0a0;
                border: 1px solid #d0cec5;
            }

            QCheckBox {
                padding-top: 6px;
                padding-bottom: 6px;
            }

            QGroupBox {
                font-weight: bold;
                border: 1px solid #d6d3c7;
                border-radius: 6px;
                margin-top: 10px;
                background-color: #f3f1ec;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 6px;
                font-size: 15px;
                color: #5a5a5a;
            }

            QListWidget {
                font-size: 13px;
                background-color: #fdfcf9;
                border: 1px solid #cfcabe;
                border-radius: 5px;
            }

            QListWidget::item {
                padding: 10px;
                color: #4a4a4a;
            }

            QListWidget::item:selected {
                background-color: #cfdcd2;
                color: #333;
            }

            QListWidget::item:hover {
                background-color: #e0e0e0;
                color: #333;
            }

            QToolButton {
                background-color: #e5e2d7;
                border: 1px solid #b8b4a8;
                padding: 6px 12px;
                border-radius: 5px;
                color: #4a4a4a;
            }

            QToolButton::menu-indicator {
                image: none;
            }

            QToolButton:hover:enabled {
                background-color: #d8d5c9;
            }

            QToolButton:disabled {
                background-color: #f0ede5;
                color: #a0a0a0;
                border: 1px solid #d0cec5;
            }
        """)
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
