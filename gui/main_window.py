from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QLineEdit, QDialog, QMessageBox
from services.publication_service import get_all_publications  # Ваш сервис для получения публикаций
from services.user_service import get_user_role
from models.relational_models import Permissions
from database.relational import get_session  
from .login import LoginDialog  # Импортируем окно входа
from .register import RegisterDialog
from .add_publication import AddPublicationDialog
from .publication_details import PublicationDetailsDialog

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.session = get_session()
        self.setWindowTitle("Система управления публикациями")
        self.setGeometry(100, 100, 800, 600)  # Увеличиваем размер окна

        layout = QVBoxLayout()

        # Поля для фильтрации
        self.search_title = QLineEdit(self)
        self.search_title.setPlaceholderText("Название публикации...")
        layout.addWidget(self.search_title)

        self.search_author = QLineEdit(self)
        self.search_author.setPlaceholderText("Имя автора...")
        layout.addWidget(self.search_author)

        self.search_journal = QLineEdit(self)
        self.search_journal.setPlaceholderText("Журнал...")
        layout.addWidget(self.search_journal)

        self.search_institution = QLineEdit(self)
        self.search_institution.setPlaceholderText("Организация...")
        layout.addWidget(self.search_institution)

        # Список публикаций
        self.publications_list = QListWidget(self)
        layout.addWidget(self.publications_list)
        self.publications_list.itemClicked.connect(self.on_publication_clicked)

        # Кнопка обновления списка
        self.refresh_button = QPushButton("Обновить список", self)
        self.refresh_button.clicked.connect(self.load_publications)
        layout.addWidget(self.refresh_button)

        # Кнопка для добавления публикации
        self.add_button = QPushButton("Добавить публикацию", self)
        self.add_button.clicked.connect(self.add_publication)
        layout.addWidget(self.add_button)

        self.setLayout(layout)
        self.publications_data = []  # Хранение загруженных публикаций
        self.load_publications()

        # Проверка роли пользователя и настройка интерфейса
        self.configure_ui_for_role()

        # Загрузка публикаций при старте
        # self.load_publications()

    def configure_ui_for_role(self):
        try:
            role = get_user_role()
        except Exception as e:
            print(f"Ошибка получения роли пользователя: {e}")
            role = None

        if role == Permissions.READ_ONLY:
            self.add_button.setEnabled(False)
        else:  # Для FULL_ACCESS и неизвестных ролей доступ открыт
            self.add_button.setEnabled(True)
    
    def add_publication(self):
        dialog = AddPublicationDialog(session=self.session)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_publications()

    def load_publications(self):
        self.publications_list.clear()  # Очистка списка перед загрузкой новых данных

        # Получаем значения фильтров
        title_filter = self.search_title.text()
        # author_filter = self.search_author.text()
        journal_filter = self.search_journal.text()
        institution_filter = self.search_institution.text()

        try:
            # Загрузка публикаций с учетом фильтров
            publications = get_all_publications(
                title=title_filter,
                # author=author_filter,
                journal=journal_filter,
                institution=institution_filter
            )

            self.publications_data = publications

            if not publications:
                self.publications_list.addItem("Не найдено публикаций.")
            else:
                for pub in publications:
                    self.publications_list.addItem(f"{pub.title} ({pub.year})")
                    # self.publications_list.addItem(f"{pub.title} ({pub.year})")

        except Exception as e:
            self.publications_list.addItem("Не удалось загрузить публикации.")  # Сообщение об ошибке загрузки
            print(f"Ошибка загрузки публикаций: {e}")
        
    def on_publication_clicked(self, item):
        index = self.publications_list.row(item)  # Получаем индекс
        publication = self.publications_data[index]  # Получаем объект публикации
        
        dialog = PublicationDetailsDialog(publication)
        dialog.exec()

# if __name__ == "__main__":
#     app = QApplication([])  # Инициализация приложения
#     init_db()  # Инициализация базы данных

#     print('opening')

#     # Показываем окно входа при старте
#     login_dialog = LoginDialog()
#     print('open')
    
#     if login_dialog.exec() == QDialog.DialogCode.Accepted:

#         print('app')
#         window = MainWindow()  # Создание окна после успешного входа
#         window.show()  # Отображение окна
#         app.exec()  # Запуск цикла обработки событий
#     else:
#         QMessageBox.warning(None, "Ошибка", "Не удалось войти в систему.")
