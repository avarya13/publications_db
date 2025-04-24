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

    data = [{
        "journal_id": j.journal_id, 
        "name": j.name,
        "type": j.type,
        "issn": j.issn,
        "isbn": j.isbn,
        "publisher": j.publisher,
        "quartile": j.quartile,
        "impact_factor": j.impact_factor,
        "website": j.website
        } for j in journals]
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
        self.setGeometry(100, 100, 800, 200)

        self.setWindowTitle("Информация о журнале")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #fdfcf9;
                font-size: 14px;
                font-family: Segoe UI, sans-serif;
            }

            QLabel {
                font-size: 13px;
                color: #3b3b3b;
                padding: 6px 4px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        def safe_label(text, value):
            return QLabel(f"{text}: {value if value else '—'}")

        layout.addWidget(safe_label("Тип", journal.get('type')))
        layout.addWidget(safe_label("Название", journal.get('name')))
        layout.addWidget(safe_label("ISSN", journal.get('issn')))
        layout.addWidget(safe_label("ISBN", journal.get('isbn')))
        layout.addWidget(safe_label("Издательство", journal.get('publisher')))
        layout.addWidget(safe_label("Квартиль", journal.get('quartile')))
        layout.addWidget(safe_label("Impact Factor", journal.get('impact_factor')))
        layout.addWidget(safe_label("Сайт", journal.get('website')))

        self.setLayout(layout)

class JournalsTab(QWidget):
    def __init__(self, session_manager):
        super().__init__()

        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
                font-family: Segoe UI, sans-serif;
                background-color: #f9f7f3;
            }

            QLineEdit {
                padding: 6px;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
                background-color: #ffffff;
            }

            QPushButton {
                padding: 8px 16px;
                background-color: #e5e2d7;
                color: #4a4a4a;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
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

            QListWidget {
                font-size: 13px;
                background-color: #fdfcf9;
                border: 1px solid #cfcabe;
                border-radius: 5px;
            }

            QLabel {
                font-size: 13px;
                color: #4a4a4a;
            }
        """)

        self.session = get_session()
        self.session_manager = session_manager

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)

        # Поисковая строка
        self.search_line_edit = QLineEdit(self)
        self.search_line_edit.setPlaceholderText("Введите название журнала для поиска...")
        self.search_line_edit.textChanged.connect(self.filter_journals)
        self.layout.addWidget(self.search_line_edit)

        # Список журналов
        self.journals_list = QListWidget(self)
        self.journals_list.itemDoubleClicked.connect(self.on_journal_double_clicked)
        self.layout.addWidget(self.journals_list)

        # Кнопки управления
        self.buttons_layout = QHBoxLayout()

        # Кнопка сортировки
        self.sort_button = QPushButton("Сортировать по алфавиту (по убыванию)", self)
        self.sort_button.clicked.connect(self.toggle_sort_order)
        self.buttons_layout.addWidget(self.sort_button)

        self.add_button = QPushButton("Добавить журнал", self)
        self.add_button.clicked.connect(self.add_journal)
        self.buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Редактировать журнал", self)
        self.edit_button.clicked.connect(self.edit_journal)
        self.buttons_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Удалить журнал", self)
        self.delete_button.clicked.connect(self.delete_journal)
        self.buttons_layout.addWidget(self.delete_button)

        self.layout.addLayout(self.buttons_layout)

        # Счётчик журналов
        self.counter_label = QLabel("Всего журналов: 0", self)
        self.layout.addWidget(self.counter_label)

        # Загрузка журналов
        self.journals_data = []
        self.load_journals()

        # Конфигурация прав
        self.configure_ui_for_role()

    def configure_ui_for_role(self):
        """Конфигурирует элементы интерфейса в зависимости от роли пользователя"""
        self.role = self.session_manager.get_user_role()
        print("ROLE", self.role)
        if self.role == UserRole.GUEST:
            # Ограниченные права для гостей
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        elif self.role == UserRole.AUTHOR:
            # Права автора
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        elif self.role == UserRole.ADMIN:
            # Права администратора
            self.add_button.setEnabled(True)
            self.edit_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            # По умолчанию
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)

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
            self.clear_journals_cache()
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
                self.clear_journals_cache()
                print(redis_client.get_cache())
                self.load_journals()

    def delete_journal(self):
        selected_item = self.journals_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите журнал для удаления.")
            return

        selected_name = selected_item.text()
        selected_journal = next(
            (journal for journal in self.journals_data if journal['name'] == selected_name),
            None
        )

        if not selected_journal:
            QMessageBox.warning(self, "Ошибка", "Не удалось найти выбранный журнал.")
            return

        confirm = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить журнал \"{selected_name}\"?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                journal_obj = self.session.query(Journal).get(selected_journal['journal_id'])
                if journal_obj:
                    self.session.delete(journal_obj)
                    self.session.commit()
                    self.clear_journals_cache()
                    print(redis_client.get_cache())
                    self.load_journals()
                else:
                    QMessageBox.warning(self, "Ошибка", "Журнал не найден в базе данных.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить журнал: {e}")

    def clear_journals_cache(self):
        for suffix in ["asc", "desc"]:
            key = f"journals:name:{suffix}"
            redis_client.delete(key)
    
    def sort_journals(self):
        """Сортирует список журналов по алфавиту в обоих направлениях."""
        if self.journals_data:
            self.journals_data.sort(key=lambda x: x['name'].lower(), reverse=False)  # Sort ascending
            self.update_journals_list(self.journals_data)


class AddJournalDialog(QDialog):
    def __init__(self, session):
        super().__init__()
        self.setWindowTitle("Добавить журнал")
        self.setGeometry(100, 100, 800, 200)
        self.session = session

        self.setStyleSheet("""
            QDialog {
                background-color: #fdfcf9;
                font-size: 14px;
                font-family: Segoe UI, sans-serif;
            }

            QLineEdit {
                padding: 6px;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
                background-color: #ffffff;
            }

            QLabel {
                font-size: 13px;
                color: #3b3b3b;
                padding: 4px;
            }

            QDialogButtonBox {
                padding-top: 10px;
            }
        """)

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

        self.publisher_line_edit = QLineEdit(self)
        self.quartile_line_edit = QLineEdit(self)
        self.impact_factor_line_edit = QLineEdit(self)
        self.website_line_edit = QLineEdit(self)

        form_layout.addRow("Издательство", self.publisher_line_edit)
        form_layout.addRow("Квартиль (Q1-Q4)", self.quartile_line_edit)
        form_layout.addRow("Impact Factor", self.impact_factor_line_edit)
        form_layout.addRow("Сайт журнала", self.website_line_edit)

        layout.addLayout(form_layout)

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
        publisher = self.publisher_line_edit.text()
        quartile = self.quartile_line_edit.text()
        impact_factor = self.impact_factor_line_edit.text()
        website = self.website_line_edit.text()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все обязательные поля.")
            return

        try:
            new_journal = Journal(
                name=name, 
                type=type_, 
                issn=issn, 
                isbn=isbn, 
                publisher=publisher,
                quartile=quartile,
                impact_factor=impact_factor,
                website=website
                )
            
            self.session.add(new_journal)
            self.session.commit()
            super().accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить журнал: {e}")


class EditJournalDialog(QDialog):
    def __init__(self, session, journal):
        super().__init__()
        self.setWindowTitle("Редактировать журнал")
        self.setGeometry(100, 100, 800, 200)
        self.session = session
        self.journal = journal

        self.setStyleSheet("""
            QDialog {
                background-color: #fdfcf9;
                font-size: 14px;
                font-family: Segoe UI, sans-serif;
            }

            QLineEdit {
                padding: 6px;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
                background-color: #ffffff;
            }

            QLabel {
                font-size: 13px;
                color: #3b3b3b;
                padding: 4px;
            }

            QDialogButtonBox {
                padding-top: 10px;
            }
        """)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.name_line_edit = QLineEdit(self)
        self.type_line_edit = QLineEdit(self)
        self.issn_line_edit = QLineEdit(self)
        self.isbn_line_edit = QLineEdit(self)
        self.publisher_line_edit = QLineEdit(self)
        self.quartile_line_edit = QLineEdit(self)
        self.impact_factor_line_edit = QLineEdit(self)
        self.website_line_edit = QLineEdit(self)

        self.name_line_edit.setText(journal['name'])
        self.type_line_edit.setText(journal['type'])
        self.issn_line_edit.setText(journal['issn'])
        self.isbn_line_edit.setText(journal['isbn'])
        self.publisher_line_edit.setText(journal['publisher'])
        self.quartile_line_edit.setText(journal['quartile'])
        self.impact_factor_line_edit.setText(journal['impact_factor'])
        self.website_line_edit.setText(journal['website'])

        form_layout.addRow("Название", self.name_line_edit)
        form_layout.addRow("Тип", self.type_line_edit)
        form_layout.addRow("ISSN", self.issn_line_edit)
        form_layout.addRow("ISBN", self.isbn_line_edit)
        form_layout.addRow("Издательство", self.publisher_line_edit)
        form_layout.addRow("Квартиль", self.quartile_line_edit)
        form_layout.addRow("Impact Factor", self.impact_factor_line_edit)
        form_layout.addRow("Сайт", self.website_line_edit)
        
        layout.addLayout(form_layout)

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
        publisher = self.publisher_line_edit.text()
        quartile = self.quartile_line_edit.text()
        impact_factor = self.impact_factor_line_edit.text()
        website = self.website_line_edit.text()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все обязательные поля.")
            return

        try:
            journal_obj = self.session.query(Journal).get(self.journal['journal_id'])
            if not journal_obj:
                QMessageBox.critical(self, "Ошибка", "Журнал не найден в базе данных.")
                return

            journal_obj.name = name
            journal_obj.type = type_
            journal_obj.issn = issn
            journal_obj.isbn = isbn
            journal_obj.publisher = publisher
            journal_obj.quartile = quartile
            journal_obj.impact_factor = impact_factor
            journal_obj.website = website

            self.session.commit()
            super().accept()

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось обновить журнал: {e}")


