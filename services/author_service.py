from database.relational import get_session
from models.relational_models import Author
from models.redis_client import redis_client
import json
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

# def get_all_authors(session, sort_by="full_name"):
#     """Retrieve all authors from the database, sorted by the given column."""
#     return session.query(Author).order_by(getattr(Author, sort_by)).all()

def get_all_authors(session, sort_by="last_name", sort_order="asc"):
    sort_order = sort_order.lower()
    if sort_order not in {"asc", "desc"}:
        raise ValueError("sort_order must be 'asc' or 'desc'")

    key = f"authors:{sort_by}:{sort_order}"
    cached = redis_client.get(key)
    if cached:
        print("Authors were loaded from Redis cache")
        return json.loads(cached)

    order_column = getattr(Author, sort_by)
    if sort_order == "desc":
        order_column = order_column.desc()

    authors = session.query(Author).order_by(order_column).all()
    data = [{"author_id": a.author_id, "full_name": a.full_name} for a in authors]
    redis_client.setex(key, 300, json.dumps(data))
    return data


class AuthorDetailsDialog(QDialog):
    def __init__(self, author):
        super().__init__()
        self.setWindowTitle("Информация об авторе")

        layout = QVBoxLayout()

        def safe_label(text, value):
            return QLabel(f"{text}: {value if value else '—'}")

        layout.addWidget(safe_label("Имя", author['first_name']))
        layout.addWidget(safe_label("Фамилия", author['last_name']))
        layout.addWidget(safe_label("Полное имя", author['full_name']))
        layout.addWidget(safe_label("Полное имя (англ.)", author['full_name_eng']))
        layout.addWidget(safe_label("Email", author['email']))
        layout.addWidget(safe_label("ORCID", author['orcid']))
        # self.counter_label = QLabel(f"Всего авторов: {total_authors_count}", self)
        # layout.addWidget(self.counter_label)

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
        self.authors_list.itemDoubleClicked.connect(self.on_author_double_clicked)

        # Кнопки для добавления и редактирования авторов
        self.buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Добавить автора", self)
        self.add_button.clicked.connect(self.add_author)
        self.buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Редактировать автора", self)
        self.edit_button.clicked.connect(self.edit_author)
        self.buttons_layout.addWidget(self.edit_button)

        self.layout.addLayout(self.buttons_layout)

        # Лейбл для отображения количества авторов
        self.counter_label = QLabel("Всего авторов: 0", self)
        self.layout.addWidget(self.counter_label)

        # Кнопки для сортировки
        self.sort_asc_button = QPushButton("Сортировать по фамилии (А-Я)", self)
        self.sort_asc_button.clicked.connect(self.sort_by_last_name_asc)
        self.layout.addWidget(self.sort_asc_button)

        self.sort_desc_button = QPushButton("Сортировать по фамилии (Я-А)", self)
        self.sort_desc_button.clicked.connect(self.sort_by_last_name_desc)
        self.layout.addWidget(self.sort_desc_button)

        # Загружаем всех авторов
        self.authors_data = []
        self.load_authors(sort_by="last_name", sort_order="asc")

    def load_authors(self, sort_by="last_name", sort_order="asc"):
        """Загружает всех авторов из базы данных."""
        try:
            authors = get_all_authors(self.session, sort_by=sort_by, sort_order=sort_order)
            self.authors_data = authors
            self.update_authors_list(authors)
            self.update_author_count()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить авторов: {e}")

    def sort_by_last_name_asc(self):
        """Сортировать авторов по фамилии в прямом порядке."""
        self.load_authors(sort_by="last_name", sort_order="asc")

    def sort_by_last_name_desc(self):
        """Сортировать авторов по фамилии в обратном порядке."""
        self.load_authors(sort_by="last_name", sort_order="desc")

    def update_author_count(self):
        """Обновляет лейбл с количеством авторов."""
        self.counter_label.setText(f"Всего авторов: {len(self.authors_list)}")

    def update_authors_list(self, authors):
        """Обновляет список авторов."""
        self.authors_list.clear()
        print(authors)
        if authors:
            for author in authors:
                self.authors_list.addItem(author['full_name'])
        else:
            self.authors_list.addItem("Не найдено авторов.")
        self.update_author_count()

    def filter_authors(self):
        """Фильтрует авторов по имени, фамилии, полному имени и полному имени (англ.)."""
        filter_text = self.search_line_edit.text().lower()
        if filter_text:
            filtered_authors = [
                author for author in self.authors_data
                if filter_text in (author['first_name'] or "").lower()
                or filter_text in (author['last_name'] or "").lower()
                or filter_text in (author['full_name'] or "").lower()
                or filter_text in (author['full_name_eng'] or "").lower()
            ]
            self.update_authors_list(filtered_authors)
        else:
            self.update_authors_list(self.authors_data)

    def on_author_double_clicked(self, item):
        """Открывает окно с информацией об авторе при двойном клике."""
        selected_name = item.text()
        selected_author = next(
            (author for author in self.authors_data if author['full_name'] == selected_name),
            None
        )
        if selected_author:
            dialog = AuthorDetailsDialog(selected_author)
            dialog.exec()

    def add_author(self):
        """Открывает диалог для добавления нового автора."""
        dialog = AddAuthorDialog(self.session)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_authors()

    def edit_author(self):
        """Открывает диалог для редактирования выбранного автора."""
        selected_item = self.authors_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите автора для редактирования.")
            return

        selected_name = selected_item.text()
        selected_author = next((author for author in self.authors_data if author['full_name'] == selected_name), None)
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

        # Полное имя (обязательное поле)
        self.full_name_label = QLabel("Полное имя*:")
        self.full_name_input = QLineEdit(self)
        self.full_name_input.setPlaceholderText("Введите полное имя")
        layout.addWidget(self.full_name_label)
        layout.addWidget(self.full_name_input)

        # Имя автора
        self.first_name_label = QLabel("Имя автора:")
        self.first_name_input = QLineEdit(self)
        self.first_name_input.setPlaceholderText("Введите имя")
        layout.addWidget(self.first_name_label)
        layout.addWidget(self.first_name_input)

        # Фамилия автора
        self.last_name_label = QLabel("Фамилия автора:")
        self.last_name_input = QLineEdit(self)
        self.last_name_input.setPlaceholderText("Введите фамилию")
        layout.addWidget(self.last_name_label)
        layout.addWidget(self.last_name_input)

        # Полное имя (англ.) 
        self.full_name_eng_label = QLabel("Полное имя (англ.):")
        self.full_name_eng_input = QLineEdit(self)
        self.full_name_eng_input.setPlaceholderText("Введите полное имя на английском")
        layout.addWidget(self.full_name_eng_label)
        layout.addWidget(self.full_name_eng_input)

        # Email автора
        self.email_label = QLabel("Email автора:")
        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("Введите email")
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)

        # ORCID автора
        self.orcid_label = QLabel("ORCID автора:")
        self.orcid_input = QLineEdit(self)
        self.orcid_input.setPlaceholderText("Введите ORCID")
        layout.addWidget(self.orcid_label)
        layout.addWidget(self.orcid_input)

        # Кнопка для добавления
        self.submit_button = QPushButton("Добавить", self)
        self.submit_button.clicked.connect(self.submit_author)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def submit_author(self):
        # Получаем данные из полей ввода
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        full_name = self.full_name_input.text().strip()
        full_name_eng = self.full_name_eng_input.text().strip() or None  
        email = self.email_input.text().strip()
        orcid = self.orcid_input.text().strip()

        # Проверяем, что обязательные поля заполнены
        if not full_name:
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля!")
            return

        # Создаем автора 
        author = Author(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            full_name_eng=full_name_eng,
            email=email,
            orcid=orcid
        )

        # Сохраняем автора в базе данных 
        self.session.add(author)
        self.session.commit()
        self.accept()

class EditAuthorDialog(QDialog):
    def __init__(self, session, author):
        super().__init__()
        self.session = session
        self.author = author
        self.setWindowTitle(f"Редактировать автора: {author['full_name']}")

        layout = QVBoxLayout()

        def add_labeled_input(label_text, initial_value=""):
            label = QLabel(label_text)
            line_edit = QLineEdit(self)
            line_edit.setText(initial_value if initial_value else "")
            layout.addWidget(label)
            layout.addWidget(line_edit)
            return line_edit

        self.full_name_input = add_labeled_input("Полное имя*", author['full_name'])
        self.first_name_input = add_labeled_input("Имя автора", author.first_name)
        self.last_name_input = add_labeled_input("Фамилия автора", author.last_name)
        self.full_name_eng_input = add_labeled_input("Полное имя (англ.)", author['full_name_eng'])
        self.email_input = add_labeled_input("Email автора", author.email)
        self.orcid_input = add_labeled_input("ORCID автора", author.orcid)

        self.submit_button = QPushButton("Сохранить", self)
        self.submit_button.clicked.connect(self.submit_edit)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def submit_edit(self):
        self.author.first_name = self.first_name_input.text()
        self.author.last_name = self.last_name_input.text()
        self.author['full_name'] = self.full_name_input.text()
        self.author['full_name_eng'] = self.full_name_eng_input.text()
        self.author.email = self.email_input.text()
        self.author.orcid = self.orcid_input.text()

        try:
            self.session.commit()
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить изменения: {e}")

# def get_all_authors(session, sort_by="full_name", sort_order="asc"):
#     order = getattr(Author, sort_by)
#     if sort_order == "desc":
#         order = order.desc()  # Descending order
#     return session.query(Author).order_by(order).all()


def get_author_by_id(session, author_id):
    return session.query(Author).filter_by(author_id=author_id).first()