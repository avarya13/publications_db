from PyQt6.QtWidgets import (QTextEdit,
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QListWidgetItem, QInputDialog,
    QListWidget, QAbstractItemView, QHBoxLayout, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt

from services.publication_service import create_publication, get_journals, get_authors, get_institutions, update_publication, get_publication_by_id
from database.document import create_publication_metadata  
from database.relational import get_session
from models.mongo import MongoDB
from models.relational_models import Publication, Author
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
    QComboBox, QListWidget, QAbstractItemView, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt


class EditPublicationDialog(QDialog):
    def __init__(self, session, publication):
        super().__init__()
        self.session = session
        self.publication = publication
        self.publication_id = publication['publication_id']
        self.setWindowTitle("Редактировать публикацию")
        self.setGeometry(200, 200, 400, 800)

        layout = QVBoxLayout()

        # Название
        self.title_input = QLineEdit()
        layout.addWidget(QLabel("Название:"))
        layout.addWidget(self.title_input)

        # Год
        self.year_input = QLineEdit()
        layout.addWidget(QLabel("Год:"))
        layout.addWidget(self.year_input)

        # Журнал
        self.journal_combo = QComboBox()
        self.load_journals()
        layout.addWidget(QLabel("Журнал:"))
        layout.addWidget(self.journal_combo)

        # Авторы
        # self.authors_list = QListWidget()
        # self.authors_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        # self.load_authors()
        # layout.addWidget(QLabel("Авторы:"))
        # layout.addWidget(self.authors_list)
        layout.addWidget(QLabel("Текущие авторы публикации:"))
        self.authors_list = QListWidget()
        self.authors_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        layout.addWidget(self.authors_list)

        layout.addWidget(QLabel("Добавить из списка доступных авторов:"))
        self.available_authors_list = QListWidget()
        self.available_authors_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        layout.addWidget(self.available_authors_list)

        authors_buttons_layout = QHBoxLayout()
        self.btn_add_to_publication = QPushButton("Добавить")
        self.btn_remove_from_publication = QPushButton("Удалить")
        authors_buttons_layout.addWidget(self.btn_add_to_publication)
        authors_buttons_layout.addWidget(self.btn_remove_from_publication)
        layout.addLayout(authors_buttons_layout)

        self.btn_add_to_publication.clicked.connect(self.add_author_to_publication)
        self.btn_remove_from_publication.clicked.connect(self.remove_author_from_publication)

        # Аннотация
        self.abstract_input = QTextEdit()
        layout.addWidget(QLabel("Аннотация:"))
        layout.addWidget(self.abstract_input)

        # Ключевые слова
        self.keyword_input = QTextEdit()
        layout.addWidget(QLabel("Ключевые слова:"))
        layout.addWidget(self.keyword_input)

        # Проекты
        self.projects_input = QLineEdit()
        layout.addWidget(QLabel("Проекты:"))
        layout.addWidget(self.projects_input)

        # Статус публикации
        self.status_input = QLineEdit()
        layout.addWidget(QLabel("Статус публикации:"))
        layout.addWidget(self.status_input)

        # Тип публикации
        self.type_input = QLineEdit()
        layout.addWidget(QLabel("Тип публикации:"))
        layout.addWidget(self.type_input)

        # DOI
        self.doi_input = QLineEdit()
        layout.addWidget(QLabel("DOI:"))
        layout.addWidget(self.doi_input)

        # Электронная библиография
        self.bibliography_input = QTextEdit()
        layout.addWidget(QLabel("Электронная библиография:"))
        layout.addWidget(self.bibliography_input)

        # Цитирования
        self.citations_wos_input = QLineEdit()
        layout.addWidget(QLabel("Цитирования WoS:"))
        layout.addWidget(self.citations_wos_input)

        self.citations_rsci_input = QLineEdit()
        layout.addWidget(QLabel("Цитирования RSCI:"))
        layout.addWidget(self.citations_rsci_input)

        self.citations_scopus_input = QLineEdit()
        layout.addWidget(QLabel("Цитирования Scopus:"))
        layout.addWidget(self.citations_scopus_input)

        self.citations_rinz_input = QLineEdit()
        layout.addWidget(QLabel("Цитирования RINZ:"))
        layout.addWidget(self.citations_rinz_input)

        self.citations_vak_input = QLineEdit()
        layout.addWidget(QLabel("Цитирования ВАК:"))
        layout.addWidget(self.citations_vak_input)

        # Дата подачи патента
        self.patent_date_input = QLineEdit()
        layout.addWidget(QLabel("Дата подачи патента:"))
        layout.addWidget(self.patent_date_input)

        # Сохранение
        self.save_button = QPushButton("Сохранить изменения")
        self.save_button.clicked.connect(self.save_changes)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

        if self.publication_id:
            self.load_publication_data()
            self.load_available_authors()

    # def load_journals(self):
    #     # Пример запроса всех журналов из БД
    #     journals = self.session.query(Journal).all()
    #     for journal in journals:
    #         self.journal_combo.addItem(journal.name, journal.id)

    # def load_authors(self):
    #     authors = self.session.query(Author).all()
    #     for author in authors:
    #         item = QListWidgetItem(author.name)
    #         item.setData(Qt.ItemDataRole.UserRole, author.author_id)
    #         self.authors_list.addItem(item)

    def load_publication_data(self):
        self.title_input.setText(self.publication.get('title', ''))
        self.year_input.setText(str(self.publication.get('year', '')))
        self.abstract_input.setPlainText(self.publication.get('abstract', ''))
        self.keyword_input.setPlainText(', '.join(self.publication.get('keywords', [])))
        self.projects_input.setText(self.publication.get('projects', ''))
        self.status_input.setText(self.publication.get('status', ''))
        self.type_input.setText(self.publication.get('type', ''))
        self.doi_input.setText(self.publication.get('doi', ''))
        self.bibliography_input.setPlainText(self.publication.get('bibliography', ''))
        self.citations_wos_input.setText(str(self.publication.get('citations_wos', '')))
        self.citations_rsci_input.setText(str(self.publication.get('citations_rsci', '')))
        self.citations_scopus_input.setText(str(self.publication.get('citations_scopus', '')))
        self.citations_rinz_input.setText(str(self.publication.get('citations_rinz', '')))
        self.citations_vak_input.setText(str(self.publication.get('citations_vak', '')))
        self.patent_date_input.setText(self.publication.get('patent_date', ''))

        # Выбор журнала
        journal_id = self.publication.get('journal_id')
        if journal_id:
            index = self.journal_combo.findData(journal_id)
            if index >= 0:
                self.journal_combo.setCurrentIndex(index)

        # Выделение авторов
        selected_author_ids = set(self.publication.get('author_ids', []))
        for i in range(self.authors_list.count()):
            item = self.authors_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) in selected_author_ids:
                item.setSelected(True)

    def save_changes(self):
        # Получение новых данных
        title = self.title_input.text()
        year = self.year_input.text()
        abstract = self.abstract_input.toPlainText()
        keywords = self.keyword_input.toPlainText()
        projects = self.projects_input.text()
        status = self.status_input.text()
        pub_type = self.type_input.text()
        doi = self.doi_input.text()
        bibliography = self.bibliography_input.toPlainText()
        citations = {
            "wos": self.citations_wos_input.text(),
            "rsci": self.citations_rsci_input.text(),
            "scopus": self.citations_scopus_input.text(),
            "rinz": self.citations_rinz_input.text(),
            "vak": self.citations_vak_input.text(),
        }
        patent_date = self.patent_date_input.text()
        journal_id = self.journal_combo.currentData()
        selected_authors = [self.authors_list.item(i).data(Qt.ItemDataRole.UserRole)
                    for i in range(self.authors_list.count())]

        # selected_authors = [self.authors_list.item(i).data(Qt.ItemDataRole.UserRole)
        #                     for i in range(self.authors_list.count())
        #                     if self.authors_list.item(i).isSelected()]

        try:
            publication = self.session.query(Publication).get(self.publication_id)
            publication.title = title
            publication.year = year
            publication.abstract = abstract
            publication.keywords = keywords
            publication.projects = projects
            publication.status = status
            publication.type = pub_type
            publication.doi = doi
            publication.bibliography = bibliography
            publication.citations_wos = citations["wos"]
            publication.citations_rsci = citations["rsci"]
            publication.citations_scopus = citations["scopus"]
            publication.citations_rinz = citations["rinz"]
            publication.citations_vak = citations["vak"]
            publication.patent_date = patent_date
            publication.journal_id = journal_id
            publication.authors = self.session.query(Author).filter(Author.author_id.in_(selected_authors)).all()

            self.session.commit()
            QMessageBox.information(self, "Успех", "Публикация обновлена.")
            self.accept()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения: {e}")

    def load_journals(self):
        """Загружает список журналов из БД"""
        self.journal_combo.clear()
        journals = get_journals(self.session)
        for journal in journals:
            self.journal_combo.addItem(f"{journal.name} ({journal.issn})", userData=journal.journal_id)

    # def load_authors(self):
    #     """Загружает список авторов из БД"""
    #     self.authors_list.clear()
    #     authors = get_authors(self.session)
    #     for author in authors:
    #         item = QListWidgetItem(author.full_name)
    #         item.setData(Qt.ItemDataRole.UserRole, author.author_id)
    #         self.authors_list.addItem(item)

    def load_authors(self):
        """Загружает текущих и доступных авторов"""
        self.authors_list.clear()
        self.available_authors_list.clear()

        all_authors = get_authors(self.session)  # Получаем всех авторов из базы
        current_authors = set(author.author_id for author in self.publication.authors)

        print('ALL', all_authors)
        print('CURRENT', current_authors)

        for author in all_authors:
            item = QListWidgetItem(author.full_name)
            item.setData(Qt.ItemDataRole.UserRole, author.author_id)
            if author.author_id in current_authors:
                self.authors_list.addItem(item)
            else:
                self.available_authors_list.addItem(item)

    def add_author_to_publication(self):
        for item in self.available_authors_list.selectedItems():
            self.available_authors_list.takeItem(self.available_authors_list.row(item))
            self.authors_list.addItem(item)

    def remove_author_from_publication(self):
        for item in self.authors_list.selectedItems():
            self.authors_list.takeItem(self.authors_list.row(item))
            self.available_authors_list.addItem(item)

    def load_available_authors(self):
        self.authors_list.clear()
        self.available_authors_list.clear()

        publication = self.session.query(Publication).get(self.publication_id)

        # Отображение текущих авторов публикации
        current_authors = publication.authors  # many-to-many связь
        current_ids = set()
        print('CUR', current_authors)

        for author in current_authors:
            item = QListWidgetItem(author.full_name)
            item.setData(Qt.ItemDataRole.UserRole, author.author_id)
            self.authors_list.addItem(item)
            current_ids.add(author.author_id)

        # Остальные авторы
        all_authors = self.session.query(Author).all()
        for author in all_authors:
            if author.author_id not in current_ids:
                item = QListWidgetItem(author.full_name)
                item.setData(Qt.ItemDataRole.UserRole, author.author_id)
                self.available_authors_list.addItem(item)

    def load_institutions(self):
        """Загружает список институтов из БД"""
        self.institutions_list.clear()
        institutions = get_institutions(self.session)
        for inst in institutions:
            self.institutions_list.addItem(f"{inst.name}")

    def load_keywords(self):
        """Загружает список авторов из БД"""
        self.keywords_list.clear()
        keywords = get_authors(self.session)
        for keyword in keywords:
            self.authors_list.addItem(f"{keyword.keyword}")

