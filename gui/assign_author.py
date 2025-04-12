from PyQt6.QtWidgets import QDialog, QComboBox, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QFormLayout
from models.relational_models import Author, User

class AssignAuthorDialog(QDialog):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Назначить пользователя автором")
        
        layout = QVBoxLayout()

        # Выпадающий список для выбора авторов
        self.author_combo = QComboBox(self)
        self.author_combo.addItem("Выберите автора", None)  # Явно указываем None как userData
        authors = self.session.query(Author).filter(Author.user == None).all()  # Только авторы, не привязанные к пользователям
        for author in authors:
            self.author_combo.addItem(author.full_name, author.author_id)
        layout.addWidget(self.author_combo)

        # Выпадающий список для выбора пользователей
        self.user_combo = QComboBox(self)
        self.user_combo.addItem("Выберите пользователя", None)  # Явно указываем None как userData
        users = self.session.query(User).filter(User.author_id == None, User.role != 'GUEST').all()  # Только свободные пользователи
        for user in users:
            self.user_combo.addItem(user.username, user.user_id)
        layout.addWidget(self.user_combo)

        # Кнопка для назначения
        self.submit_button = QPushButton("Назначить", self)
        self.submit_button.clicked.connect(self.assign_author_to_user)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def assign_author_to_user(self):
        """Назначает выбранного пользователя автором."""
        author_id = self.author_combo.currentData()
        user_id = self.user_combo.currentData()

        if author_id is None or user_id is None:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите автора и пользователя.")
            return

        author = self.session.query(Author).get(author_id)
        user = self.session.query(User).get(user_id)

        # Отладочная информация
        print("Selected author_id:", author_id)
        print("Selected user_id:", user_id)
        print("Author:", author.full_name if author else "None")
        print("User:", user.username if user else "None")

        if author and user:
            # user.author_id = author_id
            author.user = user
            self.session.commit()
            QMessageBox.information(self, "Успех", "Автор успешно назначен пользователю.")
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось назначить автора.")
