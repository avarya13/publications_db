from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QListWidgetItem, QHBoxLayout, QVBoxLayout, QTabWidget, QPushButton, QListWidget, QLineEdit, QDialog, QMessageBox, QLabel
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QPoint, Qt
from services.publication_service import get_all_publications, get_all_publications_cached  
from services.user_service import get_user_role
from services.author_service import AuthorsTab
from services.institution_service import InstitutionsTab
from services.journal_service import JournalsTab
from models.relational_models import UserRole, Publication
from database.relational import get_session  
from .login import LoginDialog
from .register import RegisterDialog
from database.relational import init_db, SessionLocal
from .add_publication import AddPublicationDialog
from .publication_details import PublicationDetailsDialog
from .edit_publication import EditPublicationDialog 
from .edit_profile import EditProfileDialog
from services.session_manager import SessionManager

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.is_admin = False

        # Инициализация базы данных
        init_db()

        self.session = SessionLocal()
        self.session_manager = SessionManager(self.session) 
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

        # # Add to the layout
        # layout.addWidget(self.profile_menu_button)

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
        self.publications_list.itemClicked.connect(self.on_publication_selected)

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
        self.authors_tab = AuthorsTab(self.session_manager)
        self.tabs.addTab(self.authors_tab, "Авторы")

        self.publishers_tab = JournalsTab(self.session_manager)
        self.tabs.addTab(self.publishers_tab, "Издательства")

        self.organizations_tab = InstitutionsTab(self.session_manager)
        self.tabs.addTab(self.organizations_tab, "Организации")

        self.setLayout(layout)

        self.login_user()

        self.publications_data = []  # To store publications data
        self.load_publications()

    def login_user(self):
        """Метод для входа пользователя в систему"""
        login_dialog = LoginDialog(self.session, self.session_manager)

        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            # Пользователь вошел успешно, получаем его роль            
            self.show()
            self.configure_ui_for_role()
        else:
            # Вход не удался, спрашиваем пользователя, хочет ли он зарегистрироваться
            choice = QMessageBox.question(self, "Ошибка", "Не удалось войти в систему. Хотите зарегистрироваться?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if choice == QMessageBox.StandardButton.Yes:
                # Открываем окно регистрации
                register_dialog = RegisterDialog(self.session, self.session_manager)

                if register_dialog.exec() == QDialog.DialogCode.Accepted:
                    QMessageBox.information(self, "Успех", "Вы успешно зарегистрированы!")
                    self.show()  
                    self.configure_ui_for_role() 
                else:
                    QMessageBox.warning(self, "Ошибка", "Регистрация не удалась.")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось войти в систему.")


    def configure_ui_for_role(self):
        """Конфигурирует элементы интерфейса в зависимости от роли пользователя"""
        try:
            role = self.session_manager.get_user_role()
            print(f"Текущая роль: {role}")

            user = self.session_manager.get_current_user()
            print(f"Текущий пользователь: {user.username}")

        except Exception as e:
            print(f"Ошибка получения роли пользователя: {e}")
            role = None

        if role == UserRole.GUEST:
            # Ограниченные права для гостей
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.configure_other_tabs()  # Настроить элементы в других вкладках
        elif role == UserRole.AUTHOR:
            # Права автора
            self.add_button.setEnabled(True)
            self.edit_button.setEnabled(False)
            self.configure_other_tabs()  # Настроить элементы в других вкладках
        elif role == UserRole.ADMIN:
            # Права администратора
            self.is_admin = True
            self.add_button.setEnabled(True)
            self.edit_button.setEnabled(True)
            self.configure_other_tabs()  # Настроить элементы в других вкладках
        else:
            # По умолчанию - только чтение
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.configure_other_tabs()  # Настроить элементы в других вкладках

    def configure_other_tabs(self):
        """Настроить элементы интерфейса в других вкладках в зависимости от роли"""
        # if hasattr(self, 'authors_tab'):
        self.authors_tab.configure_ui_for_role()

        # if hasattr(self, 'publishers_tab'):
        self.publishers_tab.configure_ui_for_role()

        # if hasattr(self, 'organizations_tab'):
        self.organizations_tab.configure_ui_for_role()
        
    def show_profile_menu(self):
        """Показывает меню профиля или окно входа"""
        role = self.session_manager.get_user_role()
        print('show_profile_menu', role)
        if role == UserRole.GUEST:
            # Если пользователь гость, то откроем окно входа
            self.login_user()
        else:
            # Меню для авторизованных пользователей
            self.profile_menu = QMenu(self)
            self.edit_profile_action = QAction("Редактировать профиль", self)
            self.logout_action = QAction("Выход", self)
            self.profile_menu.addAction(self.edit_profile_action)
            self.profile_menu.addAction(self.logout_action)

            self.edit_profile_action.triggered.connect(self.edit_profile)
            self.logout_action.triggered.connect(self.logout)

            self.profile_menu.exec(self.profile_menu_button.mapToGlobal(QPoint(0, 0)))


    # def show_profile_menu(self):
    #     """Display the profile menu"""
    #     self.profile_menu.exec(self.profile_menu_button.mapToGlobal(self.profile_menu_button.rect().bottomLeft()))

    # def get_current_user(self):
    #     """Метод для получения данных о текущем пользователе из базы данных."""
    #     if self.current_user_id is None:
    #         return None  # Если пользователь не авторизован, возвращаем None

    #     # Запросим пользователя из базы данных по его ID
    #     user = self.session.query(User).filter(User.user_id == self.current_user_id).one_or_none()
    #     return user
    
    # def edit_profile(self):
    #     """Открывает диалог редактирования профиля пользователя"""
    #     user = self.get_current_user()
    #     if user:
    #         dialog = EditProfileDialog(user=user, session=self.session)  # Передаем данные пользователя в диалог
    #         if dialog.exec() == QDialog.DialogCode.Accepted:
    #             self.load_user_info()  # Обновляем информацию после редактирования
    #     else:
    #         QMessageBox.warning(self, "Ошибка", "Не удалось найти данные пользователя.")


    def on_publication_selected(self, item):
        """Обработчик для выбора публикации из QListWidget"""
        if item is None:  # Если ничего не выбрано
            self.edit_button.setEnabled(False)
            return
        
        print('item', item)

        publication_id = item.data(Qt.ItemDataRole.UserRole)
        publication = self.session.query(Publication).get(publication_id)

        # Получаем publication_id, который мы добавили как атрибут элемента
        # publication_id = item.publication_id
        # publication = self.session.query(Publication).get(publication_id)
        
        if publication is None:
            self.edit_button.setEnabled(False)
            return

        # Получаем текущего пользователя
        current_user = self.session_manager.get_current_user()

        # Проверяем, является ли текущий пользователь автором выбранной публикации
        if current_user.role == UserRole.AUTHOR:
            # Проверяем, есть ли текущий пользователь в списке авторов
            is_author = any(author.author_id == current_user.author_id for author in publication.authors)
            if is_author:
                self.edit_button.setEnabled(True)  # Разблокируем кнопку
            else:
                self.edit_button.setEnabled(False)  # Блокируем кнопку
        else:
            self.edit_button.setEnabled(False)  # Блокируем кнопку, если пользователь не автор


    def edit_profile(self):
        """Открывает диалог редактирования профиля пользователя"""
        user = self.session_manager.get_current_user()  # Получаем текущего пользователя через менеджер сессии
        self.configure_ui_for_role()
        if user:
            # Создаем диалог для редактирования профиля и передаем менеджер сессии
            dialog = EditProfileDialog(user=user, session=self.session)  # Передаем менеджер сессии в диалог
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_user_info()  # Обновляем информацию после редактирования
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось найти данные пользователя.")

    def load_user_info(self):
        """Загружает информацию о пользователе в интерфейсе"""
        user = self.session_manager.get_current_user()
        if user:
            print(f"Текущий пользователь: {user.username}")
        else:
            print("Пользователь не найден.")

    def logout(self):
        """Функция для выхода из текущего аккаунта"""
        self.close() 
        # self.session_manager.set_user_role(UserRole.GUEST)
        # self.configure_ui_for_role()
        self.login_window = LoginDialog(self.session, self.session_manager)  # Открытие окна для нового входа
        self.login_window.show()
        self.configure_ui_for_role()
    
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
                    item = QListWidgetItem(f"{pub['title']} ({pub['year']})")  
                    item.setData(Qt.ItemDataRole.UserRole, pub['publication_id'])        
                    self.publications_list.addItem(item)               
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

        dialog = EditPublicationDialog(session=self.session, publication=publication) 

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_publications()  


    