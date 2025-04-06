from database.relational import get_session
from models.relational_models import Author
# , Coauthorship

def create_author(first_name, last_name, full_name, orcid):
    session = get_session()
    author = Author(first_name=first_name, last_name=last_name, full_name=full_name, orcid=orcid)
    session.add(author)
    session.commit()
    return author.author_id
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QHBoxLayout, QMessageBox, QWidget
from database.relational import get_session
from models.relational_models import Author
from sqlalchemy.orm import sessionmaker

def get_all_authors(session, sort_by="full_name"):
    """Retrieve all authors from the database, sorted by the given column."""
    return session.query(Author).order_by(getattr(Author, sort_by)).all()

class AuthorDetailsDialog(QDialog):
    def __init__(self, author):
        super().__init__()
        self.setWindowTitle("Информация об авторе")

        layout = QVBoxLayout()

        self.full_name_label = QLabel(f"Полное имя: {author.full_name}")
        self.email_label = QLabel(f"Email: {author.email}")
        self.orcid_label = QLabel(f"ORCID: {author.orcid}")
        self.full_name_eng_label = QLabel(f"Полное имя (англ.): {author.full_name_eng}")
        
        layout.addWidget(self.full_name_label)
        layout.addWidget(self.email_label)
        layout.addWidget(self.orcid_label)
        layout.addWidget(self.full_name_eng_label)

        self.setLayout(layout)

class AuthorsTab(QWidget):
    def __init__(self):
        super().__init__()

        self.session = get_session()
        self.layout = QVBoxLayout(self)

        # Строка поиска
        self.search_line_edit = QLineEdit(self)
        self.search_line_edit.setPlaceholderText("Введите имя автора для поиска...")
        self.search_line_edit.textChanged.connect(self.filter_authors)
        self.layout.addWidget(self.search_line_edit)

        # Список авторов
        self.authors_list = QListWidget(self)
        self.layout.addWidget(self.authors_list)
        self.authors_list.itemClicked.connect(self.on_author_clicked)

        # Кнопки для добавления и редактирования авторов
        self.buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Добавить автора", self)
        self.add_button.clicked.connect(self.add_author)
        self.buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Редактировать автора", self)
        self.edit_button.clicked.connect(self.edit_author)
        self.buttons_layout.addWidget(self.edit_button)

        self.layout.addLayout(self.buttons_layout)

        # Загружаем всех авторов
        self.authors_data = []
        self.load_authors()

    def load_authors(self):
        """Загружаем всех авторов из базы данных, сортированных по имени."""
        try:
            authors = get_all_authors(self.session)
            self.authors_data = authors
            self.update_authors_list(authors)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить авторов: {e}")

    def update_authors_list(self, authors):
        """Обновляем список авторов."""
        self.authors_list.clear()
        if authors:
            for author in authors:
                self.authors_list.addItem(author.full_name)
        else:
            self.authors_list.addItem("Не найдено авторов.")

    def filter_authors(self):
        """Фильтруем авторов по имени."""
        filter_text = self.search_line_edit.text().lower()
        filtered_authors = [author for author in self.authors_data if filter_text in author.full_name.lower()]
        self.update_authors_list(filtered_authors)

    def on_author_clicked(self, item):
        """Обработчик нажатия на имя автора из списка."""
        selected_name = item.text()
        selected_author = next((author for author in self.authors_data if author.full_name == selected_name), None)

        if selected_author:
            dialog = AuthorDetailsDialog(selected_author)
            dialog.exec()

    def add_author(self):
        """Диалог для добавления нового автора."""
        dialog = AddAuthorDialog(self.session)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_authors()

    def edit_author(self):
        """Диалог для редактирования выбранного автора."""
        selected_item = self.authors_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите автора для редактирования.")
            return

        selected_name = selected_item.text()
        selected_author = next((author for author in self.authors_data if author.full_name == selected_name), None)

        if selected_author:
            dialog = EditAuthorDialog(self.session, selected_author)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_authors()


class AddAuthorDialog(QDialog):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Добавить нового автора")
        
        layout = QVBoxLayout()

        self.first_name_label = QLabel("Имя автора:")
        self.first_name_input = QLineEdit(self)
        self.first_name_input.setPlaceholderText("Введите имя")
        layout.addWidget(self.first_name_label)
        layout.addWidget(self.first_name_input)

        self.last_name_label = QLabel("Фамилия автора:")
        self.last_name_input = QLineEdit(self)
        self.last_name_input.setPlaceholderText("Введите фамилию")
        layout.addWidget(self.last_name_label)
        layout.addWidget(self.last_name_input)

        self.email_label = QLabel("Email автора:")
        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("Введите email")
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)

        self.orcid_label = QLabel("ORCID автора:")
        self.orcid_input = QLineEdit(self)
        self.orcid_input.setPlaceholderText("Введите ORCID")
        layout.addWidget(self.orcid_label)
        layout.addWidget(self.orcid_input)

        self.submit_button = QPushButton("Добавить", self)
        self.submit_button.clicked.connect(self.submit_author)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def submit_author(self):
        first_name = self.first_name_input.text()
        last_name = self.last_name_input.text()
        email = self.email_input.text()
        orcid = self.orcid_input.text()

        if not first_name or not last_name:
            QMessageBox.warning(self, "Ошибка", "Имя и фамилия автора обязательны.")
            return

        try:
            new_author = Author(
                first_name=first_name,
                last_name=last_name,
                full_name=f"{first_name} {last_name}",
                email=email,
                orcid=orcid
            )
            self.session.add(new_author)
            self.session.commit()
            self.accept()  # Закрытие диалога
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить автора: {e}")


class EditAuthorDialog(QDialog):
    def __init__(self, session, author):
        super().__init__()
        self.session = session
        self.author = author
        self.setWindowTitle(f"Редактировать автора: {author.full_name}")

        layout = QVBoxLayout()

        self.first_name_label = QLabel("Имя автора:")
        self.first_name_input = QLineEdit(self)
        self.first_name_input.setText(self.author.first_name)
        layout.addWidget(self.first_name_label)
        layout.addWidget(self.first_name_input)

        self.last_name_label = QLabel("Фамилия автора:")
        self.last_name_input = QLineEdit(self)
        self.last_name_input.setText(self.author.last_name)
        layout.addWidget(self.last_name_label)
        layout.addWidget(self.last_name_input)

        self.email_label = QLabel("Email автора:")
        self.email_input = QLineEdit(self)
        self.email_input.setText(self.author.email)
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)

        self.orcid_label = QLabel("ORCID автора:")
        self.orcid_input = QLineEdit(self)
        self.orcid_input.setText(self.author.orcid)
        layout.addWidget(self.orcid_label)
        layout.addWidget(self.orcid_input)

        self.submit_button = QPushButton("Сохранить", self)
        self.submit_button.clicked.connect(self.submit_edit)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def submit_edit(self):
        self.author.first_name = self.first_name_input.text()
        self.author.last_name = self.last_name_input.text()
        self.author.email = self.email_input.text()
        self.author.orcid = self.orcid_input.text()
        self.author.full_name = f"{self.author.first_name} {self.author.last_name}"

        try:
            self.session.commit()
            self.accept()  
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить изменения: {e}")

def get_all_authors(session):
    return session.query(Author).all()

def get_author_by_id(session, author_id):
    return session.query(Author).filter_by(author_id=author_id).first()