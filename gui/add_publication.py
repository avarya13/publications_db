from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QComboBox, QListWidget, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from services.publication_service import create_publication, get_journals, get_authors, get_institutions

class AddPublicationDialog(QDialog):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Добавить публикацию")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        # Поле Названия
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Название")
        layout.addWidget(QLabel("Название:"))
        layout.addWidget(self.title_input)

        # Поле Года
        self.year_input = QLineEdit(self)
        self.year_input.setPlaceholderText("Год")
        layout.addWidget(QLabel("Год:"))
        layout.addWidget(self.year_input)

        # Выбор журнала
        self.journal_combo = QComboBox(self)
        self.load_journals()
        layout.addWidget(QLabel("Журнал:"))
        layout.addWidget(self.journal_combo)

        # Список авторов
        self.authors_list = QListWidget(self)
        self.load_authors()
        layout.addWidget(QLabel("Авторы:"))
        layout.addWidget(self.authors_list)

        # Кнопка добавления автора
        self.add_author_button = QPushButton("Добавить автора", self)
        self.add_author_button.clicked.connect(self.add_author)
        layout.addWidget(self.add_author_button)

        # Список институтов
        self.institutions_list = QListWidget(self)
        self.load_institutions()
        layout.addWidget(QLabel("Институты:"))
        layout.addWidget(self.institutions_list)

        # Кнопка добавления института
        self.add_institution_button = QPushButton("Добавить институт", self)
        self.add_institution_button.clicked.connect(self.add_institution)
        layout.addWidget(self.add_institution_button)

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
            self.journal_combo.addItem(f"{journal.name} ({journal.issn})", userData=journal.journal_id)

    def load_authors(self):
        """ Загружает список авторов из БД """
        self.authors_list.clear()
        authors = get_authors(self.session)
        for author in authors:
            self.authors_list.addItem(f"{author.full_name}")

    def load_institutions(self):
        """ Загружает список институтов из БД """
        self.institutions_list.clear()
        institutions = get_institutions(self.session)
        for inst in institutions:
            self.institutions_list.addItem(f"{inst.name}")

    def add_author(self):
        """ Добавляет выбранного автора в список """
        selected_item = self.authors_list.currentItem()
        if selected_item:
            selected_item.setBackground(Qt.GlobalColor.green)  # Подсвечиваем выбранного

    def add_institution(self):
        """ Добавляет выбранный институт в список """
        selected_item = self.institutions_list.currentItem()
        if selected_item:
            selected_item.setBackground(Qt.GlobalColor.green)  # Подсвечиваем выбранный

    def add_publication(self):
        """ Создает новую публикацию в базе """
        title = self.title_input.text()
        year = self.year_input.text()
        journal_id = self.journal_combo.currentData()

        selected_authors = [item.text() for item in self.authors_list.selectedItems()]
        selected_institutions = [item.text() for item in self.institutions_list.selectedItems()]

        if not title or not year.isdigit() or not journal_id or not selected_authors or not selected_institutions:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля и выберите хотя бы одного автора и институт.")
            return

        create_publication(
            session=self.session,
            title=title,
            year=int(year),
            journal_id=journal_id,
            authors=selected_authors,
            institutions=selected_institutions
        )
        self.accept()
