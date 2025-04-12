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
        self.setGeometry(200, 200, 300, 250)

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
        # self.role_combo = QComboBox(self)
        # self.role_combo.addItems([Permissions.FULL_ACCESS, Permissions.READ_ONLY, Permissions.COMBINED])
        # layout.addWidget(QLabel("Роль:"))
        # layout.addWidget(self.role_combo)

        # Кнопка для добавления пользователя
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
