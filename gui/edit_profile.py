from PyQt6.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QPushButton, QLabel

class EditProfileDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать профиль")
        self.session = session
        
        self.setLayout(QVBoxLayout())
        
        # Метка для отображения текущего имени пользователя
        self.name_label = QLabel("Имя:")
        self.layout().addWidget(self.name_label)
        
        # Поле для ввода нового имени
        self.new_name_input = QLineEdit(self)
        self.layout().addWidget(self.new_name_input)

        # Поле для ввода нового пароля (опционально)
        self.new_password_input = QLineEdit(self)
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout().addWidget(self.new_password_input)

        # Кнопка для сохранения изменений
        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.save_changes)
        self.layout().addWidget(self.save_button)
        
        self.load_user_info()

    def load_user_info(self):
        """Загружаем текущие данные пользователя и отображаем их"""
        try:
            user = get_current_user(self.session)  
            self.name_label.setText(f"Имя: {user.full_name}")
            self.new_name_input.setText(user.full_name)  
        except Exception as e:
            print(f"Не удалось загрузить данные пользователя: {e}")

    def save_changes(self):
        """Сохраняем изменения в профиле пользователя"""
        new_name = self.new_name_input.text()
        new_password = self.new_password_input.text()

        # Если изменено имя
        if new_name:
            try:
                user = get_current_user(self.session)
                user.full_name = new_name
                if new_password:
                    user.password = new_password  # Обновление пароля (если нужно)
                self.session.commit()
                self.accept()
            except Exception as e:
                print(f"Ошибка сохранения изменений: {e}")
                self.reject()

        else:
            print("Имя не может быть пустым.")
            self.reject()
