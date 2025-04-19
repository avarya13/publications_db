from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QAbstractItemView, QScrollArea,
    QComboBox, QListWidget, QHBoxLayout, QMessageBox, QWidget, QListWidgetItem, QCheckBox
)
from PyQt6.QtCore import Qt
from services.publication_service import create_publication, get_journals, get_authors, get_institutions
from models.mongo import MongoDB  

class AddPublicationDialog(QDialog):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.selected_authors = []
        self.setWindowTitle("Добавить публикацию")
        # self.showFullScreen()  # Включаем полноэкранный режим

        layout = QVBoxLayout()

        # Поле Названия (обязательное)
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Название (обязательно)")
        self.title_input.setFixedHeight(35)
        layout.addWidget(QLabel("Название:"))
        layout.addWidget(self.title_input)

        # Поле года (обязательное)
        self.year_input = QLineEdit(self)
        self.year_input.setPlaceholderText("Год (обязательно)")
        self.year_input.setFixedHeight(35)
        layout.addWidget(QLabel("Год:"))
        layout.addWidget(self.year_input)

        # Выбор журнала (поиск по подстроке)
        self.journal_combo = QComboBox(self)
        self.journal_combo.setEditable(True)
        self.load_journals()
        layout.addWidget(QLabel("Журнал:"))
        layout.addWidget(self.journal_combo)

        # Авторы
        self.author_search = QLineEdit(self)
        self.author_search.setPlaceholderText("Поиск автора...")
        self.author_search.setFixedHeight(35)
        self.author_search.textChanged.connect(self.filter_authors)
        layout.addWidget(QLabel("Авторы (обязательно):"))
        layout.addWidget(self.author_search)

        self.authors_list = QListWidget(self)
        self.authors_list.setFixedHeight(400)  
        self.load_authors()
        layout.addWidget(self.authors_list)

        # Отображение выбранных авторов
        self.selected_authors_container = QWidget()
        self.selected_authors_layout = QHBoxLayout(self.selected_authors_container)
        self.selected_authors_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.selected_authors_container)

        # Выбор института
        self.institution_combo = QComboBox(self)
        self.institution_combo.setEditable(True)
        self.load_institutions()
        layout.addWidget(QLabel("Организация (обязательно):"))
        layout.addWidget(self.institution_combo)

        # Метаданные
        self.doi_input = QLineEdit(self)
        self.doi_input.setPlaceholderText("DOI")
        self.doi_input.setFixedHeight(35)
        layout.addWidget(QLabel("DOI:"))
        layout.addWidget(self.doi_input)

        self.link_input = QLineEdit(self)
        self.link_input.setPlaceholderText("Ссылка на статью")
        self.link_input.setFixedHeight(35)
        layout.addWidget(QLabel("Ссылка:"))
        layout.addWidget(self.link_input)

        self.keywords_input = QLineEdit(self)
        self.keywords_input.setPlaceholderText("Ключевые слова (через запятую)")
        self.keywords_input.setFixedHeight(35)
        layout.addWidget(QLabel("Ключевые слова:"))
        layout.addWidget(self.keywords_input)

        # Аннотация
        self.abstract_input = QLineEdit(self)
        self.abstract_input.setPlaceholderText("Аннотация")
        self.abstract_input.setFixedHeight(60)
        layout.addWidget(QLabel("Аннотация:"))
        layout.addWidget(self.abstract_input)

        self.citations_input = QLineEdit(self)
        self.citations_input.setPlaceholderText("Цитирование")
        self.citations_input.setFixedHeight(35)
        layout.addWidget(QLabel("Цитирование:"))
        layout.addWidget(self.citations_input)

        # Проекты
        layout.addWidget(QLabel("Проекты:"))
        self.projects_input = QLineEdit()
        layout.addWidget(self.projects_input)

        # Статус публикации
        layout.addWidget(QLabel("Статус публикации:"))
        self.status_input = QLineEdit()
        layout.addWidget(self.status_input)

        # Тип публикации
        layout.addWidget(QLabel("Тип публикации:"))
        self.type_input = QLineEdit()
        layout.addWidget(self.type_input)

        # Электронная библиография
        layout.addWidget(QLabel("Электронная библиография:"))
        self.bibliography_input = QLineEdit()
        self.bibliography_input.setMinimumHeight(100)
        layout.addWidget(self.bibliography_input)

        # Цитирования
        layout.addWidget(QLabel("Цитирования WoS:"))
        self.citations_wos_input = QLineEdit()
        layout.addWidget(self.citations_wos_input)

        layout.addWidget(QLabel("Цитирования RSCI:"))
        self.citations_rsci_input = QLineEdit()
        layout.addWidget(self.citations_rsci_input)

        layout.addWidget(QLabel("Цитирования Scopus:"))
        self.citations_scopus_input = QLineEdit()
        layout.addWidget(self.citations_scopus_input)

        layout.addWidget(QLabel("Цитирования RINZ:"))
        self.citations_rinz_input = QLineEdit()
        layout.addWidget(self.citations_rinz_input)

        layout.addWidget(QLabel("Цитирования ВАК:"))
        self.citations_vak_input = QLineEdit()
        layout.addWidget(self.citations_vak_input)

        # Патент
        layout.addWidget(QLabel("Дата подачи патента:"))
        self.patent_date_input = QLineEdit()
        layout.addWidget(self.patent_date_input)

        # Выбор языка
        self.language_combo = QComboBox(self)
        self.language_combo.addItems(["Русский", "English", "Deutsch"])
        layout.addWidget(QLabel("Язык:"))
        layout.addWidget(self.language_combo)

        # Кнопка добавления публикации
        self.add_button = QPushButton("Добавить", self)
        self.add_button.clicked.connect(self.add_publication)
        layout.addWidget(self.add_button)

        # Добавление прокрутки
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(QWidget())
        scroll_area.widget().setLayout(layout)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scroll_area)

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
        """)

    def load_journals(self):
        """ Загружает список журналов из БД """
        self.journal_combo.clear()
        journals = get_journals(self.session)
        for journal in journals:
            self.journal_combo.addItem(journal.name, userData=journal.journal_id)

    def load_authors(self):
        self.authors_list.clear() 
        self.authors = get_authors(self.session) 

        print(self.authors)
        
        for author in self.authors:
            widget = QWidget()
            
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            
            checkbox = QCheckBox()
            layout.addWidget(checkbox)
            
            label = QLabel(author.full_name)
            layout.addWidget(label)
            
            checkbox.stateChanged.connect(lambda state, a=author: self.toggle_author(a, state))
            
            item = QListWidgetItem()
            item.setText(author.full_name)  
            self.authors_list.addItem(item)
            self.authors_list.setItemWidget(item, widget)  

    def filter_authors(self, search_text):
        for index in range(self.authors_list.count()):
            item = self.authors_list.item(index)
            if search_text.lower() in item.text().lower():  
                item.setHidden(False)  
            else:
                item.setHidden(True)  

    def load_institutions(self):
        """ Загружает список институтов из БД """
        self.institutions_list.clear()
        institutions = get_institutions(self.session)
        for inst in institutions:
            self.institutions_list.addItem(f"{inst.name}")

    def toggle_author(self, author, state):
        if state == Qt.CheckState.Checked.value:
            if author not in self.selected_authors:
                self.selected_authors.append(author)
                print(f"Добавлен автор: {author.full_name}")
        else:
            if author in self.selected_authors:
                self.selected_authors.remove(author)
                print(f"Удалён автор: {author.full_name}")

    def add_selected_author(self, author_name):
        label = QLabel(author_name)
        button = QPushButton("×")
        button.setFixedSize(20, 20)
        button.clicked.connect(lambda: self.remove_selected_author(author_name))
        
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(label)
        layout.addWidget(button)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.selected_authors_layout.addWidget(container)
        self.selected_authors_container.update()

    def remove_selected_author(self, author_name):
        for i in reversed(range(self.selected_authors_layout.count())):
            widget = self.selected_authors_layout.itemAt(i).widget()
            if widget:
                label = widget.findChild(QLabel)
                if label and label.text() == author_name:
                    checkbox = widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(False) 

                    self.selected_authors_layout.removeWidget(widget)  
                    widget.deleteLater()  
                    break

    def load_institutions(self):
        self.institution_combo.clear()
        institutions = get_institutions(self.session)
        for institution in institutions:
            self.institution_combo.addItem(institution.name, institution.institution_id)

    def add_publication(self):
        title = self.title_input.text().strip()
        year = self.year_input.text().strip()
        journal_id = self.journal_combo.currentData()
        institution_id = self.institution_combo.currentData()
        doi = self.doi_input.text().strip()
        link = self.link_input.text().strip()
        keywords = self.keywords_input.text().strip()
        abstract = self.abstract_input.text().strip()
        citations = self.citations_input.text().strip()
        projects=self.projects_input.text().strip(),
        status=self.status_input.text().strip(),
        type=self.type_input.text().strip(),
        bibliography=self.bibliography_input.text().strip(),
        citations_wos=self.citations_wos_input.text().strip(),
        citations_rsci=self.citations_rsci_input.text().strip(),
        citations_scopus=self.citations_scopus_input.text().strip(),
        citations_rinz=self.citations_rinz_input.text().strip(),
        citations_vak=self.citations_vak_input.text().strip(),
        patent_date=self.patent_date_input.text().strip(),
        language=self.language_combo.currentText()

        # Проверка обязательных полей
        if not title or not year or not self.selected_authors or not institution_id:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все обязательные поля.")
            return

        try:
            # Передаем только ID авторов, а не объекты
            author_ids = [author.author_id for author in self.selected_authors]

            # Сохраняем публикацию
            publication_id = create_publication(self.session, title, year, journal_id, author_ids, keywords)

            mongo_client = MongoDB()

            # Создаем метаданные для публикации
            mongo_client.create_publication_metadata(
                publication_id=publication_id,
                doi=doi,
                link=link,
                abstract=abstract,
                citations=citations,
                language=language, 
                projects=projects,
                status=status,
                type=type,
                bibliography=bibliography,
                citations_wos=citations_wos,
                citations_rsci=citations_rsci,
                citations_scopus=citations_scopus,
                citations_rinz=citations_rinz,
                citations_vak=citations_vak,
                patent_date=patent_date,
            )

            QMessageBox.information(self, "Успешно", "Публикация добавлена.")
            self.accept()  # Закрыть диалог с результатом accept()

        except Exception as e:
            print(f"Не удалось сохранить публикацию:\n{str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить публикацию:\n{str(e)}")
