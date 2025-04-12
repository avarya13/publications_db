from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QPushButton, QListWidget, QLineEdit, QDialog, QMessageBox, QLabel
from services.publication_service import get_all_publications, get_all_publications_cached  # Ваш сервис для получения публикаций
from services.user_service import get_user_role
from services.author_service import AuthorsTab
from services.institution_service import InstitutionsTab
from services.journal_service import JournalsTab
from models.relational_models import Permissions
from database.relational import get_session  
from .login import LoginDialog  # Импортируем окно входа
from .register import RegisterDialog
from .add_publication import AddPublicationDialog
from .publication_details import PublicationDetailsDialog
from .edit_publication import EditPublicationDialog  

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.session = get_session()
        self.setWindowTitle("Система управления публикациями")
        self.setGeometry(100, 100, 800, 600)

        # Основной макет
        layout = QVBoxLayout()

        # Создание TabWidget для вкладок
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs)

        # Вкладка поиска публикаций
        self.search_tab = QWidget()
        self.search_layout = QVBoxLayout(self.search_tab)

        self.search_title = QLineEdit(self)
        self.search_title.setPlaceholderText("Название публикации...")
        self.search_layout.addWidget(self.search_title)

        self.search_author = QLineEdit(self)
        self.search_author.setPlaceholderText("Имя автора...")
        self.search_layout.addWidget(self.search_author)

        self.search_journal = QLineEdit(self)
        self.search_journal.setPlaceholderText("Журнал...")
        self.search_layout.addWidget(self.search_journal)

        self.search_institution = QLineEdit(self)
        self.search_institution.setPlaceholderText("Организации...")
        self.search_layout.addWidget(self.search_institution)

        self.search_keyword = QLineEdit(self)
        self.search_keyword.setPlaceholderText("Ключевое слово...")
        self.search_layout.addWidget(self.search_keyword)

        # Список публикаций
        self.publications_list = QListWidget(self)
        self.search_layout.addWidget(self.publications_list)
        self.publications_list.itemDoubleClicked.connect(self.on_publication_double_clicked)

        self.num_pub_label = QLabel(self)
        self.num_pub_label.setText("Количество публикаций: 0")
        self.search_layout.addWidget(self.num_pub_label)

        # Кнопка обновления списка
        self.refresh_button = QPushButton("Обновить список", self)
        self.refresh_button.clicked.connect(self.load_publications)
        self.search_layout.addWidget(self.refresh_button)

        # Кнопка для добавления публикации
        self.add_button = QPushButton("Добавить публикацию", self)
        self.add_button.clicked.connect(self.add_publication)
        self.search_layout.addWidget(self.add_button)

        # Кнопка для редактирования публикации
        self.edit_button = QPushButton("Редактировать публикацию", self)
        self.edit_button.clicked.connect(self.edit_publication)
        self.search_layout.addWidget(self.edit_button)
        self.tabs.addTab(self.search_tab, "Поиск публикаций")

        # Вкладка с авторами
        self.authors_tab = AuthorsTab()
        self.authors_layout = QVBoxLayout(self.authors_tab)
        self.authors_list = QListWidget(self)
        self.authors_layout.addWidget(self.authors_list)
        self.tabs.addTab(self.authors_tab, "Авторы")

        # Вкладка с издательствами
        self.publishers_tab = JournalsTab()
        self.publishers_layout = QVBoxLayout(self.publishers_tab)
        self.publishers_list = QListWidget(self)
        self.publishers_layout.addWidget(self.publishers_list)
        self.tabs.addTab(self.publishers_tab, "Издательства")

        # Вкладка с организациями
        self.organizations_tab = InstitutionsTab()
        self.organizations_layout = QVBoxLayout(self.organizations_tab)
        self.organizations_list = QListWidget(self)
        self.organizations_layout.addWidget(self.organizations_list)
        self.tabs.addTab(self.organizations_tab, "Организации")

        self.setLayout(layout)
        self.publications_data = []  
        self.load_publications()

        # self.tabs.currentChanged.connect(self.on_tab_changed)

        self.configure_ui_for_role()

    # def on_tab_changed(self, index):
    #     if index == 1:  
    #         self.load_authors()
    #     elif index == 0: 
    #         self.load_publications()

    def configure_ui_for_role(self):
        try:
            role = get_user_role()
        except Exception as e:
            print(f"Ошибка получения роли пользователя: {e}")
            role = None

        if role == Permissions.READ_ONLY:
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)  
        else: 
            self.add_button.setEnabled(True)
            self.edit_button.setEnabled(True)
    
    def add_publication(self):
        dialog = AddPublicationDialog(session=self.session)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_publications()

    def load_publications(self):
        self.publications_list.clear() 
        
        title_filter = self.search_title.text()
        author_filter = self.search_author.text()
        journal_filter = self.search_journal.text()
        institution_filter = self.search_institution.text()
        keyword_filter = self.search_keyword.text()

        try:
            publications = get_all_publications_cached(
                self.session,
                title=title_filter,
                author=author_filter,
                journal=journal_filter,
                institution=institution_filter, 
                keyword=keyword_filter
            )

            # self.publications_data = publications
            # num_pub = len(publications)  
            # self.num_pub_label.setText(f"Количество публикаций: {num_pub}")

            # if not publications:
            #     self.publications_list.addItem("Не найдено публикаций.")
            # else:
            #     for pub in publications:
            #         self.publications_list.addItem(f"{pub.title} ({pub.year})")

            self.publications_data = publications
            num_pub = len(publications)  
            self.num_pub_label.setText(f"Количество публикаций: {num_pub}")

            if not publications:
                self.publications_list.addItem("Не найдено публикаций.")
            else:
                for pub in publications:
                    self.publications_list.addItem(f"{pub['title']} ({pub['year']})")

        except Exception as e:
            self.publications_list.addItem("Не удалось загрузить публикации.") 
            print(f"Ошибка загрузки публикаций: {e}")

    def on_publication_double_clicked(self, item):
        index = self.publications_list.row(item)
        publication = self.publications_data[index]
        dialog = PublicationDetailsDialog(publication)
        dialog.exec()

    def edit_publication(self):
        """Открытие диалога редактирования для выбранной публикации"""
        selected_item = self.publications_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите публикацию для редактирования.")
            return

        index = self.publications_list.row(selected_item)
        publication = self.publications_data[index]
        print(publication)

        dialog = EditPublicationDialog(session=self.session, publication=publication)  # Передаем объект и сессию

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_publications()  

    def on_author_clicked(self, item):
        pass

    def on_publisher_clicked(self, item):
        pass

    def on_organization_clicked(self, item):
        pass

    