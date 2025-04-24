from PyQt6.QtWidgets import QToolButton, QGroupBox, QWidget, QMenu, QListWidgetItem, QHBoxLayout, QVBoxLayout, QTabWidget, QPushButton, QListWidget, QLineEdit, QDialog, QMessageBox, QLabel
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QToolButton
from PyQt6.QtCore import Qt

from PyQt6.QtCore import QPoint, Qt
from services.publication_service import clear_publication_cache, get_all_publications_cached  
from services.user_service import get_user_role
from services.author_service import AuthorsTab
from services.institution_service import InstitutionsTab
from services.journal_service import JournalsTab
from models.relational_models import UserRole, Publication, PublicationAuthor, PublicationKeyword
from models.mongo import MongoDB
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

        self.is_author = False 

        init_db()

        self.session = SessionLocal()
        self.session_manager = SessionManager(self.session) 

        self.setWindowTitle("Система управления публикациями")
        self.setGeometry(100, 100, 800, 600)

        # --- Main Layout ---
        layout = QVBoxLayout()

        # --- Header Layout ---
        header_layout = QHBoxLayout()
        header_layout.addStretch()

        # Profile menu as ToolButton with dropdown
        self.profile_menu = QMenu(self)
        self.edit_profile_action = QAction("Редактировать профиль", self)
        self.logout_action = QAction("Сменить аккаунт", self)
        self.profile_menu.addAction(self.edit_profile_action)
        self.profile_menu.addAction(self.logout_action)

        self.profile_menu_button = QToolButton(self)
        self.profile_menu_button.setText("Профиль")
        self.profile_menu_button.setMenu(self.profile_menu)
        self.profile_menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)


        self.edit_profile_action.triggered.connect(self.edit_profile)
        self.logout_action.triggered.connect(self.logout)

        header_layout.addWidget(self.profile_menu_button)
        layout.addLayout(header_layout)

        # --- Tab Widget ---
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs)

        # --- Search Tab ---
        self.search_tab = QWidget()
        self.search_layout = QVBoxLayout(self.search_tab)
        self.search_layout.setContentsMargins(10, 10, 10, 10)
        self.search_layout.setSpacing(10)

        # --- Search Filters Group ---
        # --- Search Tab ---
        self.search_tab = QWidget()
        self.search_layout = QVBoxLayout(self.search_tab)
        self.search_layout.setContentsMargins(10, 10, 10, 10)
        self.search_layout.setSpacing(10)

        # --- Search Filters Group ---
        search_fields_group = QGroupBox("Фильтры поиска")
        search_fields_layout = QVBoxLayout()

        # Создание и добавление заголовков
        self.search_title_label = QLabel("Название публикации")
        self.search_author_label = QLabel("Имя автора")
        self.search_journal_label = QLabel("Журнал")
        self.search_institution_label = QLabel("Организация")
        self.search_keyword_label = QLabel("Ключевое слово")

        # Создание и настройка полей ввода
        self.search_title = QLineEdit(self)
        self.search_title.setPlaceholderText("Название публикации...")
        self.search_author = QLineEdit(self)
        self.search_author.setPlaceholderText("Имя автора...")
        self.search_journal = QLineEdit(self)
        self.search_journal.setPlaceholderText("Журнал...")
        # self.search_institution = QLineEdit(self)
        # self.search_institution.setPlaceholderText("Организация...")
        self.search_keyword = QLineEdit(self)
        self.search_keyword.setPlaceholderText("Ключевое слово...")

        # Добавление заголовков и полей ввода в layout
        search_fields_layout.addWidget(self.search_title_label)
        search_fields_layout.addWidget(self.search_title)

        search_fields_layout.addWidget(self.search_author_label)
        search_fields_layout.addWidget(self.search_author)

        search_fields_layout.addWidget(self.search_journal_label)
        search_fields_layout.addWidget(self.search_journal)

        # search_fields_layout.addWidget(self.search_institution_label)
        # search_fields_layout.addWidget(self.search_institution)

        search_fields_layout.addWidget(self.search_keyword_label)
        search_fields_layout.addWidget(self.search_keyword)

        # Установка layout для группы фильтров
        search_fields_group.setLayout(search_fields_layout)
        self.search_layout.addWidget(search_fields_group)

        # --- Publication List ---
        self.publications_list = QListWidget(self)
        self.publications_list.setAlternatingRowColors(True)
        self.publications_list.itemDoubleClicked.connect(self.on_publication_double_clicked)
        self.publications_list.itemClicked.connect(self.on_publication_selected)
        self.search_layout.addWidget(self.publications_list)

        self.num_pub_label = QLabel("Количество публикаций: 0", self)
        self.search_layout.addWidget(self.num_pub_label)

        # --- Sorting Buttons ---
        sort_buttons_layout = QHBoxLayout()
        self.sort_year_button = QPushButton("Сортировать по году ↑")
        self.sort_year_button.clicked.connect(self.toggle_sort_by_year)
        sort_buttons_layout.addWidget(self.sort_year_button)

        self.sort_alpha_button = QPushButton("Сортировать по алфавиту ↑")
        self.sort_alpha_button.clicked.connect(self.toggle_sort_by_title)
        sort_buttons_layout.addWidget(self.sort_alpha_button)

        self.search_layout.addLayout(sort_buttons_layout)

        # Состояния сортировки
        self.sort_by_year_asc = True
        self.sort_by_title_asc = True
        self.current_sort = None  # "year" или "title"

        # --- Control Buttons ---
        self.refresh_button = QPushButton("Обновить список", self)
        self.refresh_button.clicked.connect(self.load_publications)

        self.add_button = QPushButton("Добавить публикацию", self)
        # self.add_button.setIcon(QIcon("icons/add.png"))  # если есть иконки

        self.edit_button = QPushButton("Редактировать публикацию", self)
        # self.edit_button.setIcon(QIcon("icons/edit.png"))

        self.delete_button = QPushButton("Удалить публикацию", self)
        # self.delete_button.setIcon(QIcon("icons/delete.png"))

        self.add_button.clicked.connect(self.add_publication)
        self.edit_button.clicked.connect(self.edit_publication)
        self.delete_button.clicked.connect(self.delete_publication)

        for button in [self.refresh_button, self.add_button, self.edit_button, self.delete_button]:
            button.setFixedHeight(35)
            self.search_layout.addWidget(button)

        self.tabs.addTab(self.search_tab, "Поиск публикаций")

        # --- Other Tabs ---
        self.authors_tab = AuthorsTab(self.session_manager)
        self.tabs.addTab(self.authors_tab, "Авторы")

        self.publishers_tab = JournalsTab(self.session_manager)
        self.tabs.addTab(self.publishers_tab, "Журналы")

        self.organizations_tab = InstitutionsTab(self.session_manager)
        self.tabs.addTab(self.organizations_tab, "Организации")

        self.setLayout(layout)

        # --- Login and Load ---
        self.login_user()
        self.publications_data = []  
        self.load_publications()

        # --- Optional Styling ---
        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
                font-family: Segoe UI, sans-serif;
                background-color: #f9f7f3;
            }
                           
            QLabel {  background-color: #f3f1ec;}

            QPushButton {
                padding: 8px 16px;
                background-color: #e5e2d7;
                color: #4a4a4a;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
            }

            QPushButton:hover:enabled {
                background-color: #d8d5c9;
                color: #333;  /* Изменить цвет текста на тёмный */
            }

            QPushButton:disabled {
                background-color: #f0ede5;
                color: #a0a0a0;
                border: 1px solid #d0cec5;
            }

            QGroupBox {
                font-weight: bold;
                border: 1px solid #d6d3c7;
                border-radius: 6px;
                margin-top: 10px;
                background-color: #f3f1ec;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 6px;
                font-size: 15px;
                color: #5a5a5a;
            }

            QListWidget {
                font-size: 13px;
                background-color: #fdfcf9;
                border: 1px solid #cfcabe;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 10px;
                color: #4a4a4a;  /* Text color */
            }
            QListWidget::item:selected {
                background-color: #cfdcd2;
                color: #333;  /* Darker text color when selected */
            }
            QListWidget::item:hover {
                background-color: #e0e0e0;  /* Lighter background color on hover */
                color: #333;  /* Darker text color on hover */
            }

            QToolButton {
                background-color: #e5e2d7;
                border: 1px solid #b8b4a8;
                padding: 6px 12px;
                border-radius: 5px;
                color: #4a4a4a;
            }
            QToolButton::menu-indicator {
                image: none;
            }
            QToolButton:hover:enabled {
                background-color: #d8d5c9;
            }
            QToolButton:disabled {
                background-color: #f0ede5;
                color: #a0a0a0;
                border: 1px solid #d0cec5;
            }
        """)

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
            self.role = self.session_manager.get_user_role()
            print(f"Текущая роль: {self.role}")

            user = self.session_manager.get_current_user()
            print(f"Текущий пользователь: {user.username}")

        except Exception as e:
            print(f"Ошибка получения роли пользователя: {e}")
            self.role = None

        if self.role == UserRole.GUEST:
            # Ограниченные права для гостей
            self.delete_button.setEnabled(False)
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.configure_other_tabs()  
        elif self.role == UserRole.AUTHOR:
            # Права автора
            self.delete_button.setEnabled(False)
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.configure_other_tabs()  
        elif self.role == UserRole.ADMIN:
            # Права администратора
            self.delete_button.setEnabled(True)
            self.add_button.setEnabled(True)
            self.edit_button.setEnabled(True)
            self.configure_other_tabs()  
        else:
            # По умолчанию - только чтение
            self.delete_button.setEnabled(False)
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.configure_other_tabs()  

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
        self.role = self.session_manager.get_user_role()
        # print('show_profile_menu', role)
        if self.role == UserRole.GUEST:
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
            is_author = current_user.author and any(author.author_id == current_user.author.author_id for author in publication.authors)

            # is_author = any(author.author_id == current_user.author_id for author in publication.authors)
            if is_author:
                self.edit_button.setEnabled(True) 
                self.is_author = True 
            else:
                self.edit_button.setEnabled(False) 
                self.is_author = False  
        elif current_user.role == UserRole.ADMIN:
            self.edit_button.setEnabled(True)  
            self.is_author = True 
        else:
            self.is_author = False  
            self.edit_button.setEnabled(False)  # Блокируем кнопку, если пользователь не автор

    def delete_publication(self):
        """Удаляет выбранную публикацию (только для администратора)"""
        selected_item = self.publications_list.currentItem()

        if not selected_item:
            QMessageBox.warning(self, "Ошибка", "Выберите публикацию для удаления.")
            return

        publication_id = selected_item.data(Qt.ItemDataRole.UserRole)
        publication = self.session.query(Publication).get(publication_id)

        if not publication:
            QMessageBox.warning(self, "Ошибка", "Публикация не найдена.")
            return

        confirm = QMessageBox.question(self, "Подтвердите удаление",
                                    f"Вы уверены, что хотите удалить публикацию:\n{publication.title}?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                # Удаляем связи с авторами
                self.session.query(PublicationAuthor).filter_by(publication_id=publication_id).delete()
                # Удаляем связи с ключевыми словами
                self.session.query(PublicationKeyword).filter_by(publication_id=publication_id).delete()

                # Удаляем саму публикацию
                self.session.delete(publication)
                self.session.commit()

                # Удаляем мета-данные из MongoDB
                mongo_db = MongoDB()
                mongo_db.delete_metadata(publication_id)

                QMessageBox.information(self, "Успех", "Публикация удалена.")
                clear_publication_cache()
                self.load_publications()

            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить публикацию.\n{str(e)}")


        # if confirm == QMessageBox.StandardButton.Yes:
        #     try:
        #         self.session.delete(publication)
        #         self.session.commit()
        #         QMessageBox.information(self, "Успех", "Публикация удалена.")
        #         clear_publication_cache()
        #         self.load_publications()
        #     except Exception as e:
        #         self.session.rollback()
        #         QMessageBox.critical(self, "Ошибка", f"Не удалось удалить публикацию.\n{str(e)}")

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
            clear_publication_cache()
            self.load_publications()

    def load_publications(self):
        self.publications_list.clear() 
        
        title_filter = self.search_title.text()
        author_filter = self.search_author.text()
        journal_filter = self.search_journal.text()
        # institution_filter = self.search_institution.text()
        keyword_filter = self.search_keyword.text()

        try:
            publications = get_all_publications_cached(
                self.session,
                title=title_filter,
                author=author_filter,
                journal=journal_filter,
                # institution=institution_filter, 
                keyword=keyword_filter
            )

            self.publications_data = publications

            # Применим сортировку
            if self.current_sort == "year":
                self.publications_data.sort(
                    key=lambda x: x["year"],
                    reverse=not self.sort_by_year_asc
                )
            elif self.current_sort == "title":
                self.publications_data.sort(
                    key=lambda x: x["title"].lower(),
                    reverse=not self.sort_by_title_asc
                )

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

    def toggle_sort_by_year(self):
        self.sort_by_year_asc = not self.sort_by_year_asc
        self.current_sort = "year"
        arrow = "↑" if self.sort_by_year_asc else "↓"
        self.sort_year_button.setText(f"Сортировать по году {arrow}")
        self.sort_alpha_button.setText("Сортировать по алфавиту ↑")  # reset
        self.load_publications()

    def toggle_sort_by_title(self):
        self.sort_by_title_asc = not self.sort_by_title_asc
        self.current_sort = "title"
        arrow = "↑" if self.sort_by_title_asc else "↓"
        self.sort_alpha_button.setText(f"Сортировать по алфавиту {arrow}")
        self.sort_year_button.setText("Сортировать по году ↑")  # reset
        self.load_publications()

    def on_publication_double_clicked(self, item):
        index = self.publications_list.row(item)
        self.selected_publication_index = index  # сохраняем для редактирования
        publication = self.publications_data[index]
        dialog = PublicationDetailsDialog(publication)
        dialog.exec()

    def edit_publication(self):
        """Открытие диалога редактирования для выбранной публикации"""
        selected_item = self.publications_list.currentItem()

        if not selected_item and hasattr(self, "selected_publication_index"):
            index = self.selected_publication_index
        elif selected_item:
            index = self.publications_list.row(selected_item)
            self.selected_publication_index = index
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите публикацию для редактирования.")
            return

        publication = self.publications_data[index]
        dialog = EditPublicationDialog(session=self.session, publication=publication, user_role=self.role, is_author_of_publication=self.is_author)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            clear_publication_cache()
            self.load_publications()


