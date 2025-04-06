from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QAbstractItemView,
    QComboBox, QListWidget, QHBoxLayout, QMessageBox, QWidget, QListWidgetItem, QCheckBox
)
from PyQt6.QtCore import Qt
from services.publication_service import create_publication, get_journals, get_authors, get_institutions
from database.document import create_publication_metadata  

class AddPublicationDialog(QDialog):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Добавить публикацию")
        self.setGeometry(200, 200, 500, 500)

        layout = QVBoxLayout()

        # Поле Названия (обязательное)
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Название (обязательно)")
        layout.addWidget(QLabel("Название:"))
        layout.addWidget(self.title_input)

        # Поле года (обязательное)
        self.year_input = QLineEdit(self)
        self.year_input.setPlaceholderText("Год (обязательно)")
        layout.addWidget(QLabel("Год:"))
        layout.addWidget(self.year_input)

        # Выбор журнала (поиск по подстроке)
        self.journal_combo = QComboBox(self)
        self.journal_combo.setEditable(True)
        self.load_journals()
        layout.addWidget(QLabel("Журнал:"))
        layout.addWidget(self.journal_combo)

        # Список авторов с множественным выбором и поиском
        # self.authors_list = QListWidget(self)
        # self.authors_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        # self.author_search = QLineEdit(self)
        # self.author_search.setPlaceholderText("Поиск автора...")
        # self.author_search.textChanged.connect(self.filter_authors)
        # layout.addWidget(QLabel("Авторы (обязательно):"))
        # layout.addWidget(self.author_search)
        # layout.addWidget(self.authors_list)
        # self.load_authors()

        self.author_search = QLineEdit(self)
        self.author_search.setPlaceholderText("Поиск автора...")
        self.author_search.textChanged.connect(self.filter_authors)
        layout.addWidget(QLabel("Авторы (обязательно):"))
        layout.addWidget(self.author_search)
        
        self.authors_list = QListWidget(self)
        self.load_authors()
        layout.addWidget(self.authors_list)

        # Отображение выбранных авторов
        self.selected_authors_container = QWidget()
        self.selected_authors_layout = QHBoxLayout(self.selected_authors_container)
        self.selected_authors_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.selected_authors_container)

        # Список институтов с множественным выбором и поиском
        self.institution_combo = QComboBox(self)
        self.institution_combo.setEditable(True)
        self.load_institutions()
        layout.addWidget(QLabel("Организация (обязательно):"))
        layout.addWidget(self.institution_combo)

        # self.institutions_list = QListWidget(self)
        # self.institutions_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        # self.institution_search = QLineEdit(self)
        # self.institution_search.setPlaceholderText("Поиск института...")
        # self.institution_search.textChanged.connect(self.filter_institutions)
        # layout.addWidget(QLabel("Организация (обязательно):"))
        # layout.addWidget(self.institution_search)
        # layout.addWidget(self.institutions_list)
        # self.load_institutions()

        # Поля для метаданных
        self.doi_input = QLineEdit(self)
        self.doi_input.setPlaceholderText("DOI")
        layout.addWidget(QLabel("DOI:"))
        layout.addWidget(self.doi_input)

        self.link_input = QLineEdit(self)
        self.link_input.setPlaceholderText("Ссылка на статью")
        layout.addWidget(QLabel("Ссылка:"))
        layout.addWidget(self.link_input)

        self.keywords_input = QLineEdit(self)
        self.keywords_input.setPlaceholderText("Ключевые слова (через запятую)")
        layout.addWidget(QLabel("Ключевые слова:"))
        layout.addWidget(self.keywords_input)

        self.abstract_input = QLineEdit(self)
        self.abstract_input.setPlaceholderText("Аннотация")
        layout.addWidget(QLabel("Аннотация:"))
        layout.addWidget(self.abstract_input)

        self.citations_input = QLineEdit(self)
        self.citations_input.setPlaceholderText("Цитирования")
        layout.addWidget(QLabel("Цитирования:"))
        layout.addWidget(self.citations_input)

        # Выбор языка через ComboBox
        self.language_combo = QComboBox(self)
        self.language_combo.addItems(["Русский", "English", "Deutsch"])
        layout.addWidget(QLabel("Язык:"))
        layout.addWidget(self.language_combo)

        # Кнопка добавления публикации
        self.add_button = QPushButton("Добавить", self)
        self.add_button.clicked.connect(self.add_publication)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def load_journals(self):
        """ Загружает список журналов из БД """
        self.journal_combo.clear()
        journals = get_journals(self.session)
        for journal in journals:
            self.journal_combo.addItem(journal.name, userData=journal.journal_id)

    # def load_authors(self):
    #     """ Загружает список авторов из БД """
    #     self.authors_list.clear()
    #     authors = get_authors(self.session)
    #     for author in authors:
    #         self.authors_list.addItem(f"{author.full_name}")

    # def load_authors(self):
    #     self.authors_list.clear()
    #     self.authors = get_authors(self.session)
    #     for author in self.authors:
    #         item = QListWidgetItem(author.full_name)
    #         checkbox = QCheckBox()
    #         self.authors_list.addItem(item)
    #         self.authors_list.setItemWidget(item, checkbox)
    #         checkbox.stateChanged.connect(lambda state, a=author: self.toggle_author(a, state))


    # def load_authors(self):
    #     self.authors_list.clear()
    #     self.authors = get_authors(self.session)

    #     print(self.authors)
        
    #     for author in self.authors:
    #         widget = QWidget()
            
    #         layout = QHBoxLayout(widget)
    #         layout.setContentsMargins(0, 0, 0, 0)
            
    #         checkbox = QCheckBox()
    #         layout.addWidget(checkbox)
            
    #         label = QLabel(author.full_name)
    #         layout.addWidget(label)
            
    #         checkbox.stateChanged.connect(lambda state, a=author: self.toggle_author(a, state))
            
    #         item = QListWidgetItem()
    #         self.authors_list.addItem(item)
    #         self.authors_list.setItemWidget(item, widget)


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

    # def load_authors(self):
    #     self.authors_list.clear()  # Очищаем список
    #     self.authors = get_authors(self.session)  # Получаем список авторов
        
    #     for author in self.authors:
    #         container = QWidget()
    #         layout = QHBoxLayout(container) 
            
    #         label = QLabel(author.full_name)  
    #         checkbox = QCheckBox()  
            
    #         layout.addWidget(label)
    #         layout.addWidget(checkbox)
            
    #         item = QListWidgetItem()
    #         self.authors_list.addItem(item)  
    #         self.authors_list.setItemWidget(item, container) 
    #         checkbox.stateChanged.connect(lambda state, a=author: self.toggle_author(a, state))
    

    def load_institutions(self):
        """ Загружает список институтов из БД """
        self.institutions_list.clear()
        institutions = get_institutions(self.session)
        for inst in institutions:
            self.institutions_list.addItem(f"{inst.name}")

    # def filter_authors(self, text):
    #     """Фильтрует список авторов по введенному тексту"""
    #     self.authors_list.clear()
    #     filtered = [a for a in self.authors if text.lower() in a.lower()]
    #     self.authors_list.addItems(filtered)


    # def filter_authors(self):
    #     query = self.author_search.text().lower()
    #     for i in range(self.authors_list.count()):
    #         item = self.authors_list.item(i)
    #         item.setHidden(query not in item.text().lower())

    def toggle_author(self, author, state):
        if state == Qt.CheckState.Checked.value:
            self.add_selected_author(author.full_name)
        else:
            self.remove_selected_author(author.full_name)

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

    # def remove_selected_author(self, author_name):
    #     for i in reversed(range(self.selected_authors_layout.count())):
    #         widget = self.selected_authors_layout.itemAt(i).widget()
    #         if widget and widget.findChild(QLabel).text() == author_name:
    #             widget.deleteLater()
    #             break

    # def remove_selected_author(self, author_name):
    #     for i in reversed(range(self.selected_authors_layout.count())):
    #         widget = self.selected_authors_layout.itemAt(i).widget()
    #         if widget:
    #             # Находим QLabel внутри widget и сравниваем с именем автора
    #             label = widget.findChild(QLabel)
    #             if label and label.text() == author_name:
    #                 checkbox = widget.findChild(QCheckBox)
    #                 if checkbox:
    #                     checkbox.setChecked(False)  # Снимаем галочку с чекбокса

    #                 widget.deleteLater()
    #                 break

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


    # def filter_institutions(self, text):
    #     """Фильтрует список институтов по введенному тексту"""
    #     self.institutions_list.clear()
    #     filtered = [self.institutions_list.item(i).text() for i in range(self.institutions_list.count()) if text.lower() in self.institutions_list.item(i).text().lower()]

    #     self.institutions_list.addItems(filtered)

    # def add_publication(self):
    #     """ Создает новую публикацию в базе """
    #     title = self.title_input.text()
    #     year = self.year_input.text()
    #     journal_id = self.journal_combo.currentData()

    #     selected_authors = [item.text() for item in self.authors_list.selectedItems()]
    #     selected_institutions = [item.text() for item in self.institutions_list.selectedItems()]

    #     if not title or not year.isdigit() or not journal_id or not selected_authors or not selected_institutions:
    #         QMessageBox.warning(self, "Ошибка", "Заполните все поля и выберите хотя бы одного автора и институт.")
    #         return

    def add_publication(self):
        title = self.title_input.text().strip()
        year = self.year_input.text().strip()
        journal_id = self.journal_combo.currentData()
        institution_id = self.institution_combo.currentData()
        
        try:
            year = int(year)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Год должен быть числом.")
            return

        if not title or not journal_id or not institution_id:
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля.")
            return
        
        QMessageBox.information(self, "Успех", "Публикация успешно добавлена!")