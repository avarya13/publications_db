from PyQt6.QtWidgets import (QTextEdit, QWidget,
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QListWidgetItem, QInputDialog,
    QListWidget, QAbstractItemView, QHBoxLayout, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt

from services.publication_service import create_publication, get_journals, get_authors, get_institutions, update_publication, get_publication_by_id
# from database.document import create_publication_metadata  
from database.relational import get_session
from models.mongo import MongoDB
from models.relational_models import Publication, Author, Journal, Keyword
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
    QComboBox, QListWidget, QAbstractItemView, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from models.relational_models import UserRole
from sqlalchemy import func
from services.publication_service import clear_publication_cache
from models.mongo import MongoDB

class EditPublicationDialog(QDialog):
    def __init__(self, session=None, publication=None, user_role=None, is_author_of_publication=False):
        super().__init__()
        self.session = session
        self.publication = publication or {}
        self.publication_id = self.publication.get('publication_id', None)

        self.setWindowTitle("Редактировать публикацию")
        self.setGeometry(100, 100, 600, 700)

        self.user_role = user_role
        self.is_author_of_publication = is_author_of_publication

        # Применяем стиль
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

            QLineEdit:focus {
                border-color: #6e6e6e;
            }

            QLabel {
                font-weight: bold;
                color: #4a4a4a;
            }

            QComboBox {
                padding: 6px;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
                background-color: #ffffff;
            }

            QComboBox:focus {
                border-color: #6e6e6e;
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

            QListWidget::item {
                padding: 10px;
                color: #4a4a4a;
            }

            QListWidget::item:selected {
                background-color: #cfdcd2;
                color: #333;
            }

            QListWidget::item:hover {
                background-color: #e0e0e0;
                color: #333;
            }

            QTextEdit {
                padding: 6px;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
                background-color: #ffffff;
            }

            QTextEdit:focus {
                border-color: #6e6e6e;
            }
        """)

        # Контент формы
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)

        # Название
        form_layout.addWidget(QLabel("Название:"))
        self.title_input = QLineEdit()
        form_layout.addWidget(self.title_input)

        # Год
        form_layout.addWidget(QLabel("Год:"))
        self.year_input = QLineEdit()
        form_layout.addWidget(self.year_input)

        # Журнал
        form_layout.addWidget(QLabel("Журнал:"))
        self.journal_combo = QComboBox()
        form_layout.addWidget(self.journal_combo)

        # Текущие авторы
        form_layout.addWidget(QLabel("Текущие авторы публикации:"))
        self.authors_list = QListWidget()
        self.authors_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.authors_list.setMinimumHeight(150)
        form_layout.addWidget(self.authors_list)

        # Доступные авторы
        form_layout.addWidget(QLabel("Добавить из списка доступных авторов:"))
        self.available_authors_list = QListWidget()
        self.available_authors_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.available_authors_list.setMinimumHeight(200)
        form_layout.addWidget(self.available_authors_list)

        # Кнопки добавления/удаления авторов
        authors_buttons_layout = QHBoxLayout()
        self.btn_add_to_publication = QPushButton("Добавить")
        self.btn_remove_from_publication = QPushButton("Удалить")
        authors_buttons_layout.addWidget(self.btn_add_to_publication)
        authors_buttons_layout.addWidget(self.btn_remove_from_publication)
        form_layout.addLayout(authors_buttons_layout)

        # Аннотация
        form_layout.addWidget(QLabel("Аннотация:"))
        self.abstract_input = QTextEdit()
        self.abstract_input.setMinimumHeight(200)
        form_layout.addWidget(self.abstract_input)

        # Ключевые слова
        form_layout.addWidget(QLabel("Ключевые слова:"))
        self.keyword_input = QTextEdit()
        self.keyword_input.setMinimumHeight(100)
        form_layout.addWidget(self.keyword_input)

        # Проекты
        form_layout.addWidget(QLabel("Проекты:"))
        self.projects_input = QLineEdit()
        form_layout.addWidget(self.projects_input)

        # Статус публикации
        form_layout.addWidget(QLabel("Статус публикации:"))
        self.status_input = QLineEdit()
        form_layout.addWidget(self.status_input)

        # Тип публикации
        form_layout.addWidget(QLabel("Тип публикации:"))
        self.type_input = QLineEdit()
        form_layout.addWidget(self.type_input)

        # DOI
        form_layout.addWidget(QLabel("DOI:"))
        self.doi_input = QLineEdit()
        form_layout.addWidget(self.doi_input)

        # Ссылка
        form_layout.addWidget(QLabel("Ссылка:"))
        self.link_input = QLineEdit()
        form_layout.addWidget(self.link_input)

        # Электронная библиография
        form_layout.addWidget(QLabel("Электронная библиография:"))
        self.bibliography_input = QTextEdit()
        self.bibliography_input.setMinimumHeight(100)
        form_layout.addWidget(self.bibliography_input)

        # Цитирование
        form_layout.addWidget(QLabel("Цитирование:"))
        self.citation_input = QLineEdit()
        form_layout.addWidget(self.citation_input)

        form_layout.addWidget(QLabel("Цитируется WoS:"))
        self.citations_wos_input = QLineEdit()
        form_layout.addWidget(self.citations_wos_input)

        form_layout.addWidget(QLabel("Цитируется RSCI:"))
        self.citations_rsci_input = QLineEdit()
        form_layout.addWidget(self.citations_rsci_input)

        form_layout.addWidget(QLabel("Цитируется Scopus:"))
        self.citations_scopus_input = QLineEdit()
        form_layout.addWidget(self.citations_scopus_input)

        form_layout.addWidget(QLabel("Цитируется RINZ:"))
        self.citations_rinz_input = QLineEdit()
        form_layout.addWidget(self.citations_rinz_input)

        form_layout.addWidget(QLabel("Цитируется ВАК:"))
        self.citations_vak_input = QLineEdit()
        form_layout.addWidget(self.citations_vak_input)

        # Патент
        form_layout.addWidget(QLabel("Дата подачи патента:"))
        self.patent_date_input = QLineEdit()
        form_layout.addWidget(self.patent_date_input)

        # Язык
        form_layout.addWidget(QLabel("Язык:"))
        self.language_input = QLineEdit()
        form_layout.addWidget(self.language_input)

        # Кнопка сохранения
        self.save_button = QPushButton("Сохранить изменения")
        self.save_button.clicked.connect(self.save_changes)
        form_layout.addWidget(self.save_button)

        # ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)

        # Основной layout диалога
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

        # Загрузка данных публикации
        if self.publication_id:
            self.load_publication_data()
            self.load_available_authors()
            self.load_journals()
        
        # Конфигурируем доступность полей в зависимости от роли
        self.configure_ui_for_role()


    def load_journals(self):
        # Пример запроса всех журналов из БД
        journals = self.session.query(Journal).all()
        for journal in journals:
            self.journal_combo.addItem(journal.name)

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
        self.link_input.setText(self.publication.get('link', ''))
        self.bibliography_input.setPlainText(self.publication.get('bibliography', ''))
        self.citation_input.setText(str(self.publication.get('citations', '')))
        self.citations_wos_input.setText(str(self.publication.get('citations_wos', '')))
        self.citations_rsci_input.setText(str(self.publication.get('citations_rsci', '')))
        self.citations_scopus_input.setText(str(self.publication.get('citations_scopus', '')))
        self.citations_rinz_input.setText(str(self.publication.get('citations_rinz', '')))
        self.citations_vak_input.setText(str(self.publication.get('citations_vak', '')))
        self.patent_date_input.setText(self.publication.get('patent_date', ''))
        self.language_input.setText(self.publication.get('language', ''))

        journal_id = self.publication.get('journal_id')
        if journal_id:
            journal = self.session.query(Journal).filter(Journal.journal_id == journal_id).first()
            if journal:
                # Assuming your journal_combo box expects the journal's name to be displayed
                journal_name = journal.name
                # Now find the index of the journal in the combo box
                index = self.journal_combo.findText(journal_name)  # Assuming findText looks for the name of the journal
                if index >= 0:
                    self.journal_combo.setCurrentIndex(index)

        # Выбор журнала
        # journal_id = self.publication.get('journal_id')
        # if journal_id:
        #     index = self.journal_combo.findData(journal_id)
        #     if index >= 0:
        #         self.journal_combo.setCurrentIndex(index)

        # Выделение авторов
        selected_author_ids = set(self.publication.get('author_ids', []))
        for i in range(self.authors_list.count()):
            item = self.authors_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) in selected_author_ids:
                item.setSelected(True)

            # Загружаем метаданные из MongoDB
        mongo_db = MongoDB()
        metadata = mongo_db.get_metadata(self.publication_id)
        
        if metadata:
            # Заполняем поля метаданных
            self.abstract_input.setPlainText(metadata.get("abstract", ""))
            self.projects_input.setText(metadata.get("projects", ""))
            self.status_input.setText(metadata.get("status", ""))
            self.type_input.setText(metadata.get("type", ""))
            self.doi_input.setText(metadata.get("doi", ""))
            self.link_input.setText(metadata.get("link", ""))
            self.language_input.setText(metadata.get("language", ""))
            self.bibliography_input.setPlainText(metadata.get("bibliography", ""))
            self.citation_input.setText(metadata.get("citations", ""))
            self.patent_date_input.setText(metadata.get("patent_date", ""))
            
            # Заполняем данные о цитировании
            self.citations_wos_input.setText(metadata.get("wos", ""))
            self.citations_rsci_input.setText(metadata.get("rsci", ""))
            self.citations_scopus_input.setText(metadata.get("scopus", ""))
            self.citations_rinz_input.setText(metadata.get("rinz", ""))
            self.citations_vak_input.setText(metadata.get("vak", ""))
        
        return True

    def configure_ui_for_role(self):
        """Настройка доступности элементов интерфейса в зависимости от роли"""
        if self.user_role == UserRole.GUEST:
            self.set_read_only()
        elif self.user_role == UserRole.AUTHOR:
            if self.is_author_of_publication:
                print('PARTLY EDITABLE')
                self.set_editable_except_authors()
            else:
                self.set_read_only()
        elif self.user_role == UserRole.ADMIN:
            print('FULLY EDITABLE')
            self.set_fully_editable()

    def set_read_only(self):
        """Отключаем все поля"""
        self.title_input.setReadOnly(True)
        self.year_input.setReadOnly(True)
        self.journal_combo.setDisabled(True)
        self.abstract_input.setReadOnly(True)
        self.keyword_input.setReadOnly(True)
        self.projects_input.setReadOnly(True)
        self.status_input.setReadOnly(True)
        self.type_input.setReadOnly(True)
        self.doi_input.setReadOnly(True)
        self.link_input.setReadOnly(True)
        self.bibliography_input.setReadOnly(True)
        self.citation_input.setReadOnly(True)
        self.citations_wos_input.setReadOnly(True)
        self.citations_rsci_input.setReadOnly(True)
        self.citations_scopus_input.setReadOnly(True)
        self.citations_rinz_input.setReadOnly(True)
        self.citations_vak_input.setReadOnly(True)
        self.patent_date_input.setReadOnly(True)
        self.btn_add_to_publication.setDisabled(True)
        self.btn_remove_from_publication.setDisabled(True)
        self.link_input.setReadOnly(True)
        self.language_input.setReadOnly(True)
        self.citation_input.setReadOnly(True)

    def set_editable_except_authors(self):
        """Отключаем редактирование списка авторов для авторов публикации"""
        # self.set_read_only()
        self.authors_list.setDisabled(False)
        self.available_authors_list.setDisabled(False)

    def set_fully_editable(self):
        """Даем доступ ко всем полям для администраторов"""
        self.title_input.setReadOnly(False)
        self.year_input.setReadOnly(False)
        self.journal_combo.setDisabled(False)
        self.abstract_input.setReadOnly(False)
        self.keyword_input.setReadOnly(False)
        self.projects_input.setReadOnly(False)
        self.status_input.setReadOnly(False)
        self.type_input.setReadOnly(False)
        self.doi_input.setReadOnly(False)
        self.bibliography_input.setReadOnly(False)
        self.citations_wos_input.setReadOnly(False)
        self.citations_rsci_input.setReadOnly(False)
        self.citations_scopus_input.setReadOnly(False)
        self.citations_rinz_input.setReadOnly(False)
        self.citations_vak_input.setReadOnly(False)
        self.patent_date_input.setReadOnly(False)
        self.btn_add_to_publication.setDisabled(False)
        self.btn_remove_from_publication.setDisabled(False)
        self.link_input.setReadOnly(False)
        self.language_input.setReadOnly(False)
        self.citation_input.setReadOnly(False)

    def save_changes(self):
        try:
            # Get data from form inputs
            title = self.title_input.text()
            year = self.year_input.text()
            abstract = self.abstract_input.toPlainText()
            keyword_text = self.keyword_input.toPlainText()
            projects = self.projects_input.text()
            status = self.status_input.text()
            pub_type = self.type_input.text()
            doi = self.doi_input.text()
            link = self.link_input.text()
            language = self.language_input.text()
            citations = self.citation_input.text()
            bibliography = self.bibliography_input.toPlainText()
            citations_bool = {
                "wos": self.citations_wos_input.text(),
                "rsci": self.citations_rsci_input.text(),
                "scopus": self.citations_scopus_input.text(),
                "rinz": self.citations_rinz_input.text(),
                "vak": self.citations_vak_input.text(),
            }
            patent_date = self.patent_date_input.text()
            journal_id = self.journal_combo.currentData()
            
            # Get selected authors
            selected_authors = [
                self.authors_list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.authors_list.count())
            ]

            # Get publication from PostgreSQL
            publication = self.session.query(Publication).get(self.publication_id)
            if not publication:
                raise ValueError("Publication not found")

            # Update PostgreSQL fields
            publication.title = title
            publication.year = int(year) if year else None
            publication.journal_id = journal_id

            # Update authors relationship
            publication.authors = self.session.query(Author).filter(
                Author.author_id.in_(selected_authors)
            ).all()

            # Handle keywords for PostgreSQL
            if keyword_text:
                keyword_list = []
                for separator in [',', ';', '\n']:
                    if separator in keyword_text:
                        keyword_list = [k.strip() for k in keyword_text.split(separator) if k.strip()]
                        break
                
                if not keyword_list:
                    keyword_list = [keyword_text.strip()] if keyword_text.strip() else []
                
                publication.keywords = []
                for keyword_name in keyword_list:
                    keyword = self.session.query(Keyword).filter(
                        func.lower(Keyword.keyword) == func.lower(keyword_name)
                    ).first()
                    
                    if not keyword:
                        keyword = Keyword(name=keyword_name)
                        self.session.add(keyword)
                        self.session.flush()
                    
                    publication.keywords.append(keyword)

            # Prepare MongoDB data
            mongo_data = {
                "publication_id": publication.publication_id,
                "abstract": abstract,
                "projects": projects,
                "status": status,
                "type": pub_type,
                "doi": doi,
                "link": link,
                "bibliography": bibliography,
                "citations": citations,
                "citations_wos": citations_bool['wos'],
                "citations_rsci": citations_bool['rsci'],
                "citations_scopus": citations_bool['scopus'],
                "citations_rinz": citations_bool['rinz'],
                "citations_vak": citations_bool['vak'],
                "language": language,
                "patent_date": patent_date,
            }

            # Save to MongoDB
            mongo_db = MongoDB()
            mongo_db.update_metadata(publication.publication_id, mongo_data)

            # Commit PostgreSQL changes
            self.session.commit()
            clear_publication_cache()
            
            QMessageBox.information(self, "Успех", "Публикация обновлена.")
            self.accept()
            
        except ValueError as ve:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка в данных: {ve}")
        except Exception as e:
            self.session.rollback()
            print(f"Не удалось сохранить изменения: {e}")
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Не удалось сохранить изменения: {str(e)}"
            )

    def load_journals(self):
        """Загружает список журналов из БД"""
        self.journal_combo.clear()
        journals = get_journals(self.session)
        for journal in journals:
            print('JOURNAL', journal)
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

    # def add_author_to_publication(self):
    #     for item in self.available_authors_list.selectedItems():
    #         self.available_authors_list.takeItem(self.available_authors_list.row(item))
    #         self.authors_list.addItem(item)

    # def remove_author_from_publication(self):
    #     for item in self.authors_list.selectedItems():
    #         self.authors_list.takeItem(self.authors_list.row(item))
    #         self.available_authors_list.addItem(item)

    def add_author_to_publication(self):
        for item in self.available_authors_list.selectedItems():
            # Переносим автора из доступных в текущие
            author_id = item.data(Qt.ItemDataRole.UserRole)
            author = self.session.query(Author).filter(Author.author_id == author_id).first()
            if author:
                self.publication.authors.append(author)  # Добавляем в связь
                self.available_authors_list.takeItem(self.available_authors_list.row(item))
                self.authors_list.addItem(item)

    def remove_author_from_publication(self):
        for item in self.authors_list.selectedItems():
            # Переносим автора из текущих в доступные
            author_id = item.data(Qt.ItemDataRole.UserRole)
            author = self.session.query(Author).filter(Author.author_id == author_id).first()
            if author:
                self.publication.authors.remove(author)  # Убираем из связи
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

