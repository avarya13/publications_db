from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
from werkzeug.security import generate_password_hash
from models.relational_models import User, UserRole, Role, Permissions
from database.relational import SessionLocal

class RegisterDialog(QDialog):
    def __init__(self, session, session_manager):
        super().__init__()
        self.session = session
        self.session_manager = session_manager

        self.setWindowTitle("Регистрация пользователя")
        self.setMinimumWidth(400)

        self.setStyleSheet("""
            QDialog {
                background-color: #fdfcf9;
                font-size: 14px;
                font-family: Segoe UI, sans-serif;
            }

            QLabel {
                font-size: 13px;
                padding-top: 6px;
                color: #3b3b3b;
            }

            QLineEdit {
                padding: 6px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }

            QPushButton {
                padding: 8px 16px;
                background-color: #e5e2d7;
                color: #4a4a4a;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
            }

            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        layout = QVBoxLayout()

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Имя пользователя")
        layout.addWidget(QLabel("Имя пользователя:"))
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_input)

        self.register_button = QPushButton("Зарегистрировать", self)
        self.register_button.clicked.connect(self.register_user)
        layout.addWidget(self.register_button)

        self.setLayout(layout)

    def register_user(self):
        username = self.username_input.text()
        password = self.password_input.text()
        # role_name = self.role_combo.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")
            return

        hashed_password = generate_password_hash(password)
        session = SessionLocal()

        try:
            existing_user = session.query(User).filter_by(username=username).first()
            if existing_user:
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким именем уже существует.")
                return

            new_user = User(
                username=username,
                password_hash=hashed_password,
                role=UserRole.AUTHOR  
            )
            session.add(new_user)
            session.commit()

            # Устанавливаем пользователя
            self.session_manager.set_authenticated_user(new_user.user_id)

            # Устанавливаем роль пользователя
            self.session_manager.set_user_role(new_user.role)

            QMessageBox.information(self, "Успех", "Пользователь успешно зарегистрирован!")
            self.accept()

        except Exception as e:
            session.rollback()
            QMessageBox.warning(self, "Ошибка", f"Произошла ошибка: {e}")

        finally:
            session.close()
