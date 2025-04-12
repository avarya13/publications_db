from PyQt6.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QFormLayout
from PyQt6.QtCore import Qt
from werkzeug.security import generate_password_hash

class EditProfileDialog(QDialog):
    def __init__(self, user, session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать профиль")
        self.setFixedSize(400, 300)  # Fixed window size for better layout control
        self.session = session
        self.user = user  # User to be edited

        # Layout for the dialog
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Редактировать профиль пользователя")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Form layout for input fields
        form_layout = QFormLayout()

        # Current username label
        self.name_label = QLabel(f"Текущее имя: {self.user.username}")
        form_layout.addRow(self.name_label)

        # Input for new username
        self.new_name_input = QLineEdit(self)
        self.new_name_input.setText(self.user.username)  # Prefill the username
        self.new_name_input.setPlaceholderText("Введите новое имя пользователя")
        form_layout.addRow("Новое имя:", self.new_name_input)

        # Input for new password
        self.new_password_input = QLineEdit(self)
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("Введите новый пароль (оставьте пустым для сохранения старого)")
        form_layout.addRow("Новый пароль:", self.new_password_input)

        # Add form layout to main layout
        layout.addLayout(form_layout)

        # Horizontal layout for buttons
        button_layout = QHBoxLayout()

        # Save Button
        self.save_button = QPushButton("Сохранить", self)
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 5px; padding: 10px;")
        self.save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(self.save_button)

        # Cancel Button
        self.cancel_button = QPushButton("Отмена", self)
        self.cancel_button.setStyleSheet("background-color: #f44336; color: white; border-radius: 5px; padding: 10px;")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Set main layout
        self.setLayout(layout)

    def save_changes(self):
        """Save changes to the user's profile"""
        new_name = self.new_name_input.text().strip()
        new_password = self.new_password_input.text().strip()

        # Validate the new name input
        if not new_name:
            QMessageBox.warning(self, "Ошибка", "Имя не может быть пустым.")
            return

        # Update user info if changed
        try:
            if new_name != self.user.username:  # Check if the name is different
                self.user.username = new_name
            
            if new_password:  # If a new password is provided
                self.user.password = generate_password_hash(new_password)  # Hash the password
            
            self.session.commit()  # Save changes to the database
            QMessageBox.information(self, "Успех", "Профиль успешно обновлен.")
            self.accept()  # Close the dialog
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка сохранения изменений: {e}")

