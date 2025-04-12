from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QHBoxLayout, QMessageBox, QWidget, QFormLayout, QDialogButtonBox
from sqlalchemy.orm import sessionmaker
from database.relational import get_session
from models.relational_models import UserRole, Journal
from models.redis_client import redis_client
import json
import hashlib

# def make_cache_key(**kwargs):
#     key_base = json.dumps(kwargs, sort_keys=True)
#     return "publications:" + hashlib.md5(key_base.encode()).hexdigest()

def get_all_journals(session, sort_by="name", descending=False):
    key = f"journals:{sort_by}:{'desc' if descending else 'asc'}"
    cached = redis_client.get(key)
    if cached:
        print("Journals were loaded from Redis cache")
        return json.loads(cached)

    order = getattr(Journal, sort_by)
    if descending:
        order = order.desc()
    journals = session.query(Journal).order_by(order).all()

    data = [{"journal_id": j.journal_id, "name": j.name} for j in journals]
    redis_client.setex(key, 300, json.dumps(data))  # TTL 5 минут
    return data


# def get_all_journals(session, sort_by="name", descending=False):
#     """Retrieve all journals from the database, sorted by the given column."""
#     order = getattr(Journal, sort_by)
#     if descending:
#         order = order.desc()
#     return session.query(Journal).order_by(order).all()

class JournalDetailsDialog(QDialog):
    def __init__(self, journal):
        super().__init__()
        self.setWindowTitle("Информация о журнале")

        layout = QVBoxLayout()

        def safe_label(text, value):
            return QLabel(f"{text}: {value if value else '—'}")

        layout.addWidget(safe_label("Тип", journal.type))
        layout.addWidget(safe_label("Название", journal['name']))
        layout.addWidget(safe_label("ISSN", journal.issn))
        layout.addWidget(safe_label("ISBN", journal.isbn))

        self.setLayout(layout)

class JournalsTab(QWidget):
    def __init__(self, session_manager):
        super().__init__()

        self.session = get_session()
        self.layout = QVBoxLayout(self)

        self.sort_button = QPushButton("Сортировать по алфавиту (по убыванию)", self)
        self.sort_button.clicked.connect(self.toggle_sort_order)
        self.layout.addWidget(self.sort_button)

        # Строка поиска
        self.search_line_edit = QLineEdit(self)
        self.search_line_edit.setPlaceholderText("Введите название журнала для поиска...")
        self.search_line_edit.textChanged.connect(self.filter_journals)
        self.layout.addWidget(self.search_line_edit)

        # Список журналов
        self.journals_list = QListWidget(self)
        self.journals_list.itemDoubleClicked.connect(self.on_journal_double_clicked)  # Connect double-click to function
        self.layout.addWidget(self.journals_list)

        # Кнопки для добавления и редактирования журналов
        self.buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Добавить журнал", self)
        self.add_button.clicked.connect(self.add_journal)
        self.buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Редактировать журнал", self)
        self.edit_button.clicked.connect(self.edit_journal)
        self.buttons_layout.addWidget(self.edit_button)
        self.layout.addLayout(self.buttons_layout)

        # Лейбл для отображения количества журналов
        self.counter_label = QLabel("Всего журналов: 0", self)
        self.layout.addWidget(self.counter_label)

        # Загружаем все журналы
        self.journals_data = []
        self.load_journals()
        
        self.session_manager = session_manager    
        # self.role = self.session_manager.get_user_role()
        self.configure_ui_for_role()  

    def configure_ui_for_role(self):
        """Конфигурирует элементы интерфейса в зависимости от роли пользователя"""
        self.role = self.session_manager.get_user_role()
        print("ROLE", self.role)
        if self.role == UserRole.GUEST:
            # Ограниченные права для гостей
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
        elif self.role == UserRole.AUTHOR:
            # Права автора
            self.add_button.setEnabled(True)
            self.edit_button.setEnabled(True)
        elif self.role == UserRole.ADMIN:
            # Права администратора
            self.add_button.setEnabled(True)
            self.edit_button.setEnabled(True)
        else:
            # По умолчанию
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)

    def toggle_sort_order(self):
        """Toggles sorting order between ascending and descending."""
        if self.sort_button.text() == "Сортировать по алфавиту (по убыванию)":
            self.sort_button.setText("Сортировать по алфавиту (по возрастанию)")
            self.load_journals(descending=True)
        else:
            self.sort_button.setText("Сортировать по алфавиту (по убыванию)")
            self.load_journals(descending=False)

    def load_journals(self, descending=False):
        """Загружает все журналы из базы данных."""
        try:
            journals = get_all_journals(self.session, descending=descending)
            self.journals_data = journals
            self.update_journals_list(journals)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить журналы: {e}")

    def update_journals_list(self, journals):
        """Обновляет список журналов."""
        self.journals_list.clear()
        if journals:
            for journal in journals:
                self.journals_list.addItem(journal['name'])
        else:
            self.journals_list.addItem("Не найдено журналов.")
        self.counter_label.setText(f"Всего журналов: {len(self.journals_list)}")

    def filter_journals(self):
        """Фильтрует журналы по названию."""
        filter_text = self.search_line_edit.text().lower()
        if filter_text:
            filtered_journals = [
                journal for journal in self.journals_data
                if filter_text in (journal['name'] or "").lower()
            ]
            self.update_journals_list(filtered_journals)
        else:
            self.update_journals_list(self.journals_data)

    def on_journal_double_clicked(self, item):
        """Открывает окно с информацией о журнале при двойном клике."""
        selected_name = item.text()
        selected_journal = next(
            (journal for journal in self.journals_data if journal['name'] == selected_name),
            None
        )
        if selected_journal:
            dialog = JournalDetailsDialog(selected_journal)
            dialog.exec()

    def add_journal(self):
        """Открывает диалог для добавления нового журнала."""
        dialog = AddJournalDialog(self.session)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_journals()

    def edit_journal(self):
        """Открывает диалог для редактирования выбранного журнала."""
        selected_item = self.journals_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите журнал для редактирования.")
            return

        selected_name = selected_item.text()
        selected_journal = next(
            (journal for journal in self.journals_data if journal['name'] == selected_name),
            None
        )
        if selected_journal:
            dialog = EditJournalDialog(self.session, selected_journal)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_journals()

class AddJournalDialog(QDialog):
    def __init__(self, session):
        super().__init__()
        self.setWindowTitle("Добавить журнал")
        self.session = session

        # Layout for the dialog
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.name_line_edit = QLineEdit(self)
        self.type_line_edit = QLineEdit(self)
        self.issn_line_edit = QLineEdit(self)
        self.isbn_line_edit = QLineEdit(self)

        form_layout.addRow("Название", self.name_line_edit)
        form_layout.addRow("Тип", self.type_line_edit)
        form_layout.addRow("ISSN", self.issn_line_edit)
        form_layout.addRow("ISBN", self.isbn_line_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def accept(self):
        name = self.name_line_edit.text()
        type_ = self.type_line_edit.text()
        issn = self.issn_line_edit.text()
        isbn = self.isbn_line_edit.text()

        if not name or not type_ or not issn:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все обязательные поля.")
            return

        try:
            new_journal = Journal(name=name, type=type_, issn=issn, isbn=isbn)
            self.session.add(new_journal)
            self.session.commit()
            super().accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить журнал: {e}")

class EditJournalDialog(QDialog):
    def __init__(self, session, journal):
        super().__init__()
        self.setWindowTitle("Редактировать журнал")
        self.session = session
        self.journal = journal

        # Layout for the dialog
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.name_line_edit = QLineEdit(self)
        self.type_line_edit = QLineEdit(self)
        self.issn_line_edit = QLineEdit(self)
        self.isbn_line_edit = QLineEdit(self)

        self.name_line_edit.setText(journal['name'])
        self.type_line_edit.setText(journal.type)
        self.issn_line_edit.setText(journal.issn)
        self.isbn_line_edit.setText(journal.isbn)

        form_layout.addRow("Название", self.name_line_edit)
        form_layout.addRow("Тип", self.type_line_edit)
        form_layout.addRow("ISSN", self.issn_line_edit)
        form_layout.addRow("ISBN", self.isbn_line_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def accept(self):
        name = self.name_line_edit.text()
        type_ = self.type_line_edit.text()
        issn = self.issn_line_edit.text()
        isbn = self.isbn_line_edit.text()

        if not name or not type_ or not issn:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все обязательные поля.")
            return

        try:
            self.journal['name'] = name
            self.journal.type = type_
            self.journal.issn = issn
            self.journal.isbn = isbn
            self.session.commit()
            super().accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось обновить журнал: {e}")

