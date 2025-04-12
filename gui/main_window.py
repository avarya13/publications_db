from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QHBoxLayout, QVBoxLayout, QTabWidget, QPushButton, QListWidget, QLineEdit, QDialog, QMessageBox, QLabel
from PyQt6.QtGui import QAction
from services.publication_service import get_all_publications, get_all_publications_cached  
from services.user_service import get_user_role
from services.author_service import AuthorsTab
from services.institution_service import InstitutionsTab
from services.journal_service import JournalsTab
from models.relational_models import Permissions, User
from database.relational import get_session  
from .login import LoginDialog 
from .register import RegisterDialog
from .add_publication import AddPublicationDialog
from .publication_details import PublicationDetailsDialog
from .edit_publication import EditPublicationDialog 
from .edit_profile import EditProfileDialog

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.session = get_session()
        self.setWindowTitle("Система управления публикациями")
        self.setGeometry(100, 100, 800, 600)
        
        # Main layout
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        
        # Profile and logout menu button 
        self.profile_menu_button = QPushButton("Профиль", self)
        self.profile_menu_button.clicked.connect(self.show_profile_menu)
        header_layout.addStretch() 
        header_layout.addWidget(self.profile_menu_button)
        layout.addLayout(header_layout)

        # Create TabWidget for tabs
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs)

        # Add to the layout
        layout.addWidget(self.profile_menu_button)

        # Create a menu for profile-related actions
        self.profile_menu = QMenu(self)
        self.edit_profile_action = QAction("Редактировать профиль", self)
        self.logout_action = QAction("Сменить аккаунт", self)
        self.profile_menu.addAction(self.edit_profile_action)
        self.profile_menu.addAction(self.logout_action)

        # Connect actions to corresponding functions
        self.edit_profile_action.triggered.connect(self.edit_profile)
        self.logout_action.triggered.connect(self.logout)

        # Create a Tab for searching publications
        self.search_tab = QWidget()
        self.search_layout = QVBoxLayout(self.search_tab)

        # Add Search Fields and Publication List
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

        # List of publications
        self.publications_list = QListWidget(self)
        self.search_layout.addWidget(self.publications_list)
        self.publications_list.itemDoubleClicked.connect(self.on_publication_double_clicked)

        self.num_pub_label = QLabel(self)
        self.num_pub_label.setText("Количество публикаций: 0")
        self.search_layout.addWidget(self.num_pub_label)

        # Button to refresh the list
        self.refresh_button = QPushButton("Обновить список", self)
        self.refresh_button.clicked.connect(self.load_publications)
        self.search_layout.addWidget(self.refresh_button)

        # Button for adding a publication
        self.add_button = QPushButton("Добавить публикацию", self)
        self.add_button.clicked.connect(self.add_publication)
        self.search_layout.addWidget(self.add_button)

        # Button for editing a publication
        self.edit_button = QPushButton("Редактировать публикацию", self)
        self.edit_button.clicked.connect(self.edit_publication)
        self.search_layout.addWidget(self.edit_button)

        self.tabs.addTab(self.search_tab, "Поиск публикаций")

        # Create additional tabs like Authors, Journals, etc.
        self.authors_tab = AuthorsTab()
        self.tabs.addTab(self.authors_tab, "Авторы")

        self.publishers_tab = JournalsTab()
        self.tabs.addTab(self.publishers_tab, "Издательства")

        self.organizations_tab = InstitutionsTab()
        self.tabs.addTab(self.organizations_tab, "Организации")

        self.setLayout(layout)

        self.publications_data = []  # To store publications data
        self.load_publications()

        self.configure_ui_for_role()


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

    def show_profile_menu(self):
        """Display the profile menu"""
        self.profile_menu.exec(self.profile_menu_button.mapToGlobal(self.profile_menu_button.rect().bottomLeft()))

    def get_current_user(self):
        """Возвращает текущего авторизованного пользователя."""
        try:
            user_id = get_authenticated_user_id()  # Функция получения текущего пользователя (например, через сессию)
            return self.session.query(User).filter(User.user_id == user_id).one()  # Настроить под твою модель
        except Exception as e:
            print(f"Ошибка получения пользователя: {e}")
            return None

    def edit_profile(self):
        """Открывает диалог редактирования профиля пользователя"""
        user = self.get_current_user()
        if user:
            dialog = EditProfileDialog(user=user, session=self.session)  # Передаем данные пользователя в диалог
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_user_info()  # Обновляем информацию после редактирования
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось найти данные пользователя.")

    def load_user_info(self):
        """Загружает информацию о пользователе в интерфейсе"""
        user = self.get_current_user()
        if user:
            # Обновить UI с данными пользователя, например, отобразить имя
            print(f"Текущий пользователь: {user.full_name}")
        else:
            print("Пользователь не найден.")

    def logout(self):
        """Функция для выхода из текущего аккаунта"""
        self.close()  # Закрытие текущего окна
        self.login_window = LoginDialog(self.session)  # Открытие окна для нового входа
        self.login_window.show()
    
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


    