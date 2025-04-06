from PyQt6.QtWidgets import (QTextEdit,
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, 
    QListWidget, QAbstractItemView, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt

from services.publication_service import create_publication, get_journals, get_authors, get_institutions, update_publication, get_publication_by_id
from database.document import create_publication_metadata  
from database.relational import get_session
from models.mongo import MongoDB

class EditPublicationDialog(QDialog):
    def __init__(self, session, publication):
        super().__init__()
        self.session = session
        self.publication_id = publication.id  
        self.setWindowTitle("Редактировать публикацию")
        self.setGeometry(200, 200, 400, 800)  

        layout = QVBoxLayout()

        # Поле для заголовка
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Название")
        layout.addWidget(QLabel("Название:"))
        layout.addWidget(self.title_input)

        # Поле для года
        self.year_input = QLineEdit(self)
        self.year_input.setPlaceholderText("Год")
        layout.addWidget(QLabel("Год:"))
        layout.addWidget(self.year_input)

        # Поле для журнала
        self.journal_combo = QComboBox(self)
        self.load_journals()
        layout.addWidget(QLabel("Журнал:"))
        layout.addWidget(self.journal_combo)

        # Выбор авторов из списка
        self.authors_list = QListWidget(self)
        self.authors_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.load_authors()
        layout.addWidget(QLabel("Авторы:"))
        layout.addWidget(self.authors_list)

        # Поле для аннотации
        self.abstract_input = QTextEdit(self)
        self.abstract_input.setPlaceholderText("Введите аннотацию")
        self.abstract_input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.abstract_input.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(QLabel("Аннотация:"))
        layout.addWidget(self.abstract_input)

        # Поле для ключевых слов
        self.keyword_input = QTextEdit(self)
        self.keyword_input.setPlaceholderText("Введите ключевые слова через запятую")
        self.keyword_input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.keyword_input.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(QLabel("Ключевые слова:"))
        layout.addWidget(self.keyword_input)

        # Поле для проектов
        self.projects_input = QLineEdit(self)
        self.projects_input.setPlaceholderText("Проекты")
        layout.addWidget(QLabel("Проекты:"))
        layout.addWidget(self.projects_input)

        # Поле для статуса публикации
        self.status_input = QLineEdit(self)
        self.status_input.setPlaceholderText("Статус публикации")
        layout.addWidget(QLabel("Статус публикации:"))
        layout.addWidget(self.status_input)

        # Поле для типа публикации
        self.type_input = QLineEdit(self)
        self.type_input.setPlaceholderText("Тип публикации")
        layout.addWidget(QLabel("Тип публикации:"))
        layout.addWidget(self.type_input)

        # Поле для DOI
        self.doi_input = QLineEdit(self)
        self.doi_input.setPlaceholderText("DOI")
        layout.addWidget(QLabel("DOI:"))
        layout.addWidget(self.doi_input)

        # Поле для электронного библиографического описания
        self.bibliography_input = QTextEdit(self)
        self.bibliography_input.setPlaceholderText("Введите электронную библиографию")
        self.bibliography_input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.bibliography_input.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(QLabel("Электронная библиография:"))
        layout.addWidget(self.bibliography_input)

        # Поля для цитирований в различных источниках
        self.citations_wos_input = QLineEdit(self)
        self.citations_wos_input.setPlaceholderText("Цитирования WoS")
        layout.addWidget(QLabel("Цитирования WoS:"))
        layout.addWidget(self.citations_wos_input)

        self.citations_rsci_input = QLineEdit(self)
        self.citations_rsci_input.setPlaceholderText("Цитирования RSCI")
        layout.addWidget(QLabel("Цитирования RSCI:"))
        layout.addWidget(self.citations_rsci_input)

        self.citations_scopus_input = QLineEdit(self)
        self.citations_scopus_input.setPlaceholderText("Цитирования Scopus")
        layout.addWidget(QLabel("Цитирования Scopus:"))
        layout.addWidget(self.citations_scopus_input)

        self.citations_rinz_input = QLineEdit(self)
        self.citations_rinz_input.setPlaceholderText("Цитирования RINZ")
        layout.addWidget(QLabel("Цитирования RINZ:"))
        layout.addWidget(self.citations_rinz_input)

        self.citations_vak_input = QLineEdit(self)
        self.citations_vak_input.setPlaceholderText("Цитирования ВАК")
        layout.addWidget(QLabel("Цитирования ВАК:"))
        layout.addWidget(self.citations_vak_input)

        # Поле для даты подачи патента
        self.patent_date_input = QLineEdit(self)
        self.patent_date_input.setPlaceholderText("Дата подачи патента")
        layout.addWidget(QLabel("Дата подачи патента:"))
        layout.addWidget(self.patent_date_input)

        # Кнопка сохранения изменений
        self.save_button = QPushButton("Сохранить изменения", self)
        self.save_button.clicked.connect(self.save_changes)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

        if self.publication_id:
            self.load_publication_data()

    def load_publication_data(self):
        """Загружает данные существующей публикации"""

        print(self.publication_id)
        publication = get_publication_by_id(self.session, self.publication_id)
        
        self.title_input.setText(publication.title)
        self.year_input.setText(str(publication.year))
        
        journal_name = publication.journal.name if publication.journal else ""
        self.journal_combo.setCurrentText(journal_name)
        
        try:
            mongo_db = MongoDB()
            meta_data = mongo_db.get_metadata(self.publication_id)
            
            if meta_data:
                self.abstract_input.setText(meta_data.get('abstract', ''))
                self.doi_input.setText(meta_data.get('doi', ''))
                self.bibliography_input.setText(meta_data.get('electronic_bibliography', ''))
                # self.keywords_input.setText(', '.join(meta_data.get('keywords', [])))
                # self.citations_input.setText(str(meta_data.get('citations', 0)))
                # self.language_input.setText(meta_data.get('language', ''))
                self.projects_input.setText(meta_data.get('projects', '-'))
                self.status_input.setText(meta_data.get('publication_status', '-'))
                self.type_input.setText(meta_data.get('publication_type', '-'))
                self.citations_wos_input.setText(str(meta_data.get('citations_wos', '-')))
                self.citations_rsci_input.setText(str(meta_data.get('citations_rsci', '-')))
                self.citations_scopus_input.setText(str(meta_data.get('citations_scopus', '-')))
                self.citations_rinz_input.setText(str(meta_data.get('citations_rinz', '-')))
                self.citations_vak_input.setText(str(meta_data.get('citations_vak', '-')))
                self.patent_date_input.setText(meta_data.get('patent_application_date', '-'))
        except Exception as e:
            print(f"Ошибка при загрузке мета-данных из MongoDB: {e}")


    def save_changes(self):
        """Сохраняет изменения в базу данных"""
        title = self.title_input.text()
        year = self.year_input.text()
        journal_id = self.journal_combo.currentData()

        selected_authors = [item.text() for item in self.authors_list.selectedItems()]
        selected_institutions = [item.text() for item in self.institutions_list.selectedItems()]

        doi = self.doi_input.text()
        link = self.link_input.text()
        keywords = self.keywords_input.text().split(",")
        abstract = self.abstract_input.text()
        citations = self.citations_input.text()
        language = self.language_input.text()

        if not title or not year.isdigit() or not journal_id or not selected_authors or not selected_institutions:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля и выберите хотя бы одного автора и институт.")
            return

        update_publication(
            session=self.session,
            publication_id=self.publication_id,
            title=title,
            year=int(year),
            journal_id=journal_id,
            authors=selected_authors,
            institutions=selected_institutions
        )

        create_publication_metadata(doi, link, keywords, abstract, citations, language)

        self.accept()

    def load_journals(self):
        """Загружает список журналов из БД"""
        self.journal_combo.clear()
        journals = get_journals(self.session)
        for journal in journals:
            self.journal_combo.addItem(f"{journal.name} ({journal.issn})", userData=journal.journal_id)

    def load_authors(self):
        """Загружает список авторов из БД"""
        self.authors_list.clear()
        authors = get_authors(self.session)
        for author in authors:
            self.authors_list.addItem(f"{author.full_name}")

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
            self.authors_list.addItem(f"{author.full_name}")

