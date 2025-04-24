from database.relational import get_session
from PyQt6.QtWidgets import QSizePolicy
from models.relational_models import Author, UserRole
from models.redis_client import redis_client
from gui.assign_author import AssignAuthorDialog
import json
# , Coauthorship

def create_author(first_name, last_name, full_name, orcid):
    session = get_session()
    author = Author(first_name=first_name, last_name=last_name, full_name=full_name, orcid=orcid)
    session.add(author)
    session.commit()
    return author.author_id

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QHBoxLayout, QMessageBox, QWidget
from database.relational import get_session
from models.relational_models import Author
from sqlalchemy.orm import sessionmaker

# def get_all_authors(session, sort_by="full_name"):
#     """Retrieve all authors from the database, sorted by the given column."""
#     return session.query(Author).order_by(getattr(Author, sort_by)).all()

def get_all_authors(session, sort_by="last_name", sort_order="asc"):
    sort_order = sort_order.lower()
    if sort_order not in {"asc", "desc"}:
        raise ValueError("sort_order must be 'asc' or 'desc'")
    
    # redis_client.delete('authors:last_name:asc')

    key = f"authors:{sort_by}:{sort_order}"
    cached = redis_client.get(key)
    if cached:
        print("Authors were loaded from Redis cache")
        return json.loads(cached)

    order_column = getattr(Author, sort_by)
    if sort_order == "desc":
        order_column = order_column.desc()

    authors = session.query(Author).order_by(order_column).all()

    # Сохраняем все поля автора
    data = [{
        "author_id": a.author_id,
        "first_name": a.first_name,
        "mid_name": a.mid_name,
        "last_name": a.last_name,
        "full_name": a.full_name,
        "full_name_eng": a.full_name_eng,
        "email": a.email,
        "academic_degree": a.academic_degree,
        "position": a.position,
        "scopus_id": a.scopus_id,
        "h_index": a.h_index,
        "orcid": a.orcid
    } for a in authors]

    redis_client.setex(key, 300, json.dumps(data))
    return data

class AuthorDetailsDialog(QDialog):
    def __init__(self, author):
        super().__init__()
        self.setGeometry(100, 100, 500, 400)
        self.setWindowTitle("Информация об авторе")
        self.setStyleSheet("""
            QDialog {
                background-color: #fdfcf9;
                font-size: 14px;
                font-family: Segoe UI, sans-serif;
            }

            QLineEdit {
                padding: 6px;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
                background-color: #ffffff;
            }

            QLabel {
                font-size: 13px;
                color: #3b3b3b;
                padding: 1px;  /* уменьшено с 4px до 1px */
                margin: 0px;   /* полностью убраны внешние отступы */
            }

            QDialogButtonBox {
                padding-top: 10px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)  # минимальное расстояние между элементами

        def safe_label(text, value):
            label = QLabel(f"{text}: {value if value else '—'}")
            label.setContentsMargins(0, 0, 0, 0)            
            label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            label.setFixedHeight(18)  
            return label

        layout.addWidget(safe_label("Имя", author['first_name']))
        layout.addWidget(safe_label("Отчество", author['mid_name']))
        layout.addWidget(safe_label("Фамилия", author['last_name']))
        layout.addWidget(safe_label("Полное имя", author['full_name']))
        layout.addWidget(safe_label("Полное имя (англ.)", author['full_name_eng']))
        layout.addWidget(safe_label("Email", author['email']))
        layout.addWidget(safe_label("Ученая степень", author['academic_degree']))
        layout.addWidget(safe_label("Должность", author['position']))
        layout.addWidget(safe_label("ORCID", author['orcid']))
        layout.addWidget(safe_label("Scopus ID", author['scopus_id']))
        layout.addWidget(safe_label("Индекс Хирша", author['h_index']))

        self.setLayout(layout)


class AuthorsTab(QWidget):
    def __init__(self, session_manager):
        super().__init__()

        self.session = get_session()
        self.layout = QVBoxLayout(self)

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

            QLabel {
                color: #4a4a4a;
            }
        """)

        # Поиск по авторам
        self.search_line_edit = QLineEdit(self)
        self.search_line_edit.setPlaceholderText("Введите имя автора для поиска...")
        self.search_line_edit.textChanged.connect(self.filter_authors)
        self.layout.addWidget(self.search_line_edit)

        # Список авторов
        self.authors_list = QListWidget(self)
        self.layout.addWidget(self.authors_list)
        self.authors_list.itemDoubleClicked.connect(self.on_author_double_clicked)

        # Лейбл количества авторов
        self.counter_label = QLabel("Всего авторов: 0", self)
        self.layout.addWidget(self.counter_label)

        # Кнопки сортировки
        self.sort_asc_button = QPushButton("Сортировать по фамилии (А-Я)", self)
        self.sort_asc_button.clicked.connect(self.sort_by_last_name_asc)
        self.layout.addWidget(self.sort_asc_button)

        self.sort_desc_button = QPushButton("Сортировать по фамилии (Я-А)", self)
        self.sort_desc_button.clicked.connect(self.sort_by_last_name_desc)
        self.layout.addWidget(self.sort_desc_button)

        # Кнопки управления (2 строки по 2 кнопки)
        self.buttons_row1 = QHBoxLayout()
        self.add_button = QPushButton("Добавить автора", self)
        self.add_button.clicked.connect(self.add_author)
        self.buttons_row1.addWidget(self.add_button)

        self.edit_button = QPushButton("Редактировать автора", self)
        self.edit_button.clicked.connect(self.edit_author)
        self.buttons_row1.addWidget(self.edit_button)
        self.layout.addLayout(self.buttons_row1)

        self.buttons_row2 = QHBoxLayout()
        self.assign_button = QPushButton("Назначить пользователя автором", self)
        self.assign_button.clicked.connect(self.open_assign_dialog)
        self.buttons_row2.addWidget(self.assign_button)

        self.delete_button = QPushButton("Удалить автора", self)
        self.delete_button.clicked.connect(self.delete_author)
        self.buttons_row2.addWidget(self.delete_button)
        self.layout.addLayout(self.buttons_row2)

        # Выбор элемента
        self.authors_list.selectionModel().selectionChanged.connect(self.on_author_selected)

        # Загрузка данных
        self.authors_data = []
        self.load_authors(sort_by="last_name", sort_order="asc")

        self.session_manager = session_manager
        self.configure_ui_for_role()

    def configure_ui_for_role(self):
        self.role = self.session_manager.get_user_role()
        if self.role == UserRole.GUEST:
            self.assign_button.setEnabled(False)
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        elif self.role == UserRole.AUTHOR:
            self.assign_button.setEnabled(False)
            self.add_button.setEnabled(True)
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        elif self.role == UserRole.ADMIN:
            self.assign_button.setEnabled(True)
            self.add_button.setEnabled(True)
            self.edit_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)


    def on_author_selected(self, selected, deselected):
        self.role = self.session_manager.get_user_role()

        if self.role == UserRole.AUTHOR:
            # Получаем индекс выделенной строки
            selected_index = selected.indexes()[0] if selected.indexes() else None
            if selected_index is None:  # Если выделение снято
                self.edit_button.setEnabled(False)
            else:
                # Получаем full_name из первой ячейки строки
                full_name = selected_index.sibling(selected_index.row(), 0).data()  # Первый столбец с полным именем

                # Ищем автора по полному имени
                selected_author = self.session.query(Author).filter_by(full_name=full_name).one_or_none()

                if selected_author:
                    # Получаем текущего пользователя из session_manager
                    self.current_user = self.session_manager.get_current_user()

                    print(self.current_user)
                    # print('on_author_selected', self.current_user.author_id, selected_author.author_id)

                    # Проверяем, совпадает ли автор из таблицы с текущим пользователем
                    # if selected_author.author_id == self.current_user.author_id:
                    if selected_author.author_id == self.current_user.author.author_id:
                        self.edit_button.setEnabled(True)
                    else:
                        self.edit_button.setEnabled(False)
                else:
                    # Автор не найден
                    self.edit_button.setEnabled(False)

    def open_assign_dialog(self):
        """Открывает диалог для назначения пользователя автором."""
        dialog = AssignAuthorDialog(self.session)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_authors()

    def load_authors(self, sort_by="last_name", sort_order="asc"):
        """Загружает всех авторов из базы данных."""
        try:
            authors = get_all_authors(self.session, sort_by=sort_by, sort_order=sort_order)
            self.authors_data = authors
            self.update_authors_list(authors)
            self.update_author_count()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить авторов: {e}")

    def clear_authors_cache(self):
        print('Очистка кэша после удаления')
        keys = redis_client.keys("authors:*")
        for key in keys:
            redis_client.delete(key)

    def delete_author(self):
        selected_item = self.authors_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите автора для удаления.")
            return

        author_name = selected_item.text()
        author = self.session.query(Author).filter_by(full_name=author_name).first()

        if not author:
            QMessageBox.warning(self, "Ошибка", "Автор не найден.")
            return

        reply = QMessageBox.question(
            self, "Подтверждение", f"Удалить автора '{author.full_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(author)
                self.session.commit()
                self.clear_authors_cache()
                self.load_authors()
                QMessageBox.information(self, "Успех", f"Автор '{author.full_name}' удалён.")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить автора: {e}")

    def sort_by_last_name_asc(self):
        """Сортировать авторов по фамилии в прямом порядке."""
        self.load_authors(sort_by="last_name", sort_order="asc")

    def sort_by_last_name_desc(self):
        """Сортировать авторов по фамилии в обратном порядке."""
        self.load_authors(sort_by="last_name", sort_order="desc")

    def update_author_count(self):
        """Обновляет лейбл с количеством авторов."""
        self.counter_label.setText(f"Всего авторов: {len(self.authors_list)}")

    def update_authors_list(self, authors):
        """Обновляет список авторов."""
        self.authors_list.clear()
        print(authors)
        if authors:
            for author in authors:
                self.authors_list.addItem(author['full_name'])
        else:
            self.authors_list.addItem("Не найдено авторов.")
        self.update_author_count()

    def filter_authors(self):
        """Фильтрует авторов по имени, фамилии, полному имени и полному имени (англ.)."""
        filter_text = self.search_line_edit.text().lower()
        print(self.authors_data)
        if filter_text:
            filtered_authors = [
                author for author in self.authors_data
                if filter_text in (author['first_name'] or "").lower()
                or filter_text in (author['last_name'] or "").lower()
                or filter_text in (author['full_name'] or "").lower()
                or filter_text in (author['full_name_eng'] or "").lower()
            ]
            self.update_authors_list(filtered_authors)
        else:
            self.update_authors_list(self.authors_data)

    def on_author_double_clicked(self, item):
        """Открывает окно с информацией об авторе при двойном клике."""
        selected_name = item.text()
        selected_author = next(
            (author for author in self.authors_data if author['full_name'] == selected_name),
            None
        )
        if selected_author:
            dialog = AuthorDetailsDialog(selected_author)
            dialog.exec()

    def add_author(self):
        """Открывает диалог для добавления нового автора."""
        dialog = AddAuthorDialog(self.session)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.clear_authors_cache()
            self.load_authors()

    def edit_author(self):
        """Открывает диалог для редактирования выбранного автора."""
        selected_item = self.authors_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите автора для редактирования.")
            return

        selected_name = selected_item.text()
        selected_author = next((author for author in self.authors_data if author['full_name'] == selected_name), None)
        if selected_author:
            dialog = EditAuthorDialog(self.session, selected_author)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.clear_authors_cache()
                self.load_authors()


class AddAuthorDialog(QDialog):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setGeometry(100, 100, 500, 400)
        self.setWindowTitle("Добавить нового автора")
        self.setStyleSheet("""
            QDialog {
                background-color: #fdfcf9;
                font-size: 14px;
                font-family: Segoe UI, sans-serif;
            }

            QLineEdit {
                padding: 6px;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
                background-color: #ffffff;
            }

            QLabel {
                font-size: 13px;
                color: #3b3b3b;
                padding: 4px;
            }

            QDialogButtonBox {
                padding-top: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)


        # Полное имя (обязательное поле)
        self.full_name_label = QLabel("Полное имя*:")
        self.full_name_input = QLineEdit(self)
        self.full_name_input.setPlaceholderText("Введите полное имя")
        layout.addWidget(self.full_name_label)
        layout.addWidget(self.full_name_input)

        # Имя автора
        self.first_name_label = QLabel("Имя автора:")
        self.first_name_input = QLineEdit(self)
        self.first_name_input.setPlaceholderText("Введите имя")
        layout.addWidget(self.first_name_label)
        layout.addWidget(self.first_name_input)
        
        self.mid_name_label = QLabel("Отчество:")
        self.mid_name_input = QLineEdit(self)
        self.mid_name_input.setPlaceholderText("Введите отчество")
        layout.addWidget(self.mid_name_label)
        layout.addWidget(self.mid_name_input)

        # Фамилия автора
        self.last_name_label = QLabel("Фамилия автора:")
        self.last_name_input = QLineEdit(self)
        self.last_name_input.setPlaceholderText("Введите фамилию")
        layout.addWidget(self.last_name_label)
        layout.addWidget(self.last_name_input)

        # Полное имя (англ.) 
        self.full_name_eng_label = QLabel("Полное имя (англ.):")
        self.full_name_eng_input = QLineEdit(self)
        self.full_name_eng_input.setPlaceholderText("Введите полное имя на английском")
        layout.addWidget(self.full_name_eng_label)
        layout.addWidget(self.full_name_eng_input)

        # Email автора
        self.email_label = QLabel("Email автора:")
        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("Введите email")
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)

        # ORCID автора
        self.orcid_label = QLabel("ORCID автора:")
        self.orcid_input = QLineEdit(self)
        self.orcid_input.setPlaceholderText("Введите ORCID")
        layout.addWidget(self.orcid_label)
        layout.addWidget(self.orcid_input)

        self.position_label = QLabel("Должность:")
        self.position_input = QLineEdit(self)
        self.position_input.setPlaceholderText("Введите должность")
        layout.addWidget(self.position_label)
        layout.addWidget(self.position_input)

        self.academic_degree_label = QLabel("Ученая степень:")
        self.academic_degree_input = QLineEdit(self)
        self.academic_degree_input.setPlaceholderText("Введите ученую степень")
        layout.addWidget(self.academic_degree_label)
        layout.addWidget(self.academic_degree_input)

        self.h_index_label = QLabel("Индекс Хирша:")
        self.h_index_input = QLineEdit(self)
        self.h_index_input.setPlaceholderText("Введите индекс Хирша")
        layout.addWidget(self.h_index_label)
        layout.addWidget(self.h_index_input)

        self.scopus_id_label = QLabel("Scopus ID:")
        self.scopus_id_input = QLineEdit(self)
        self.scopus_id_input.setPlaceholderText("Введите Scopus ID")
        layout.addWidget(self.scopus_id_label)
        layout.addWidget(self.scopus_id_input)

        # Кнопка для добавления
        self.submit_button = QPushButton("Добавить", self)
        self.submit_button.clicked.connect(self.submit_author)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def submit_author(self):
        # Получаем данные из полей ввода
        first_name = self.first_name_input.text().strip()
        mid_name = self.mid_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        full_name = self.full_name_input.text().strip()
        full_name_eng = self.full_name_eng_input.text().strip() or None  
        email = self.email_input.text().strip()
        orcid = self.orcid_input.text().strip()
        position = self.position_input.text().strip()
        academic_degree = self.academic_degree_input.text().strip()
        h_index = self.h_index_input.text().strip()
        scopus_id = self.scopus_id_input.text().strip()

        # Проверяем, что обязательные поля заполнены
        if not full_name:
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля!")
            return

        # Создаем автора 
        author = Author(
            first_name=first_name,
            mid_name=mid_name or None,
            last_name=last_name,
            full_name=full_name,
            full_name_eng=full_name_eng,
            email=email,
            orcid=orcid,
            position=position or None,
            academic_degree=academic_degree or None,
            h_index=int(h_index) if h_index else None,
            scopus_id=scopus_id or None,
        )

        # Сохраняем автора в базе данных 
        self.session.add(author)
        self.session.commit()
        self.accept()

class EditAuthorDialog(QDialog):
    def __init__(self, session, author):
        super().__init__()
        self.setGeometry(100, 100, 500, 400)
        self.session = session
        self.author = author
        self.setWindowTitle(f"Редактировать автора: {author['full_name']}")
        self.setStyleSheet("""
            QDialog {
                background-color: #fdfcf9;
                font-size: 14px;
                font-family: Segoe UI, sans-serif;
            }

            QLineEdit {
                padding: 6px;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
                background-color: #ffffff;
            }

            QLabel {
                font-size: 13px;
                color: #3b3b3b;
                padding: 4px;
            }

            QDialogButtonBox {
                padding-top: 10px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)


        def add_labeled_input(label_text, initial_value=""):
            label = QLabel(label_text)
            line_edit = QLineEdit(self)
            line_edit.setText(initial_value if initial_value else "")
            layout.addWidget(label)
            layout.addWidget(line_edit)
            return line_edit

        self.full_name_input = add_labeled_input("Полное имя*", author['full_name'])
        self.first_name_input = add_labeled_input("Имя автора", author['first_name'])
        self.mid_name_input = add_labeled_input("Отчество", author.get('mid_name'))
        self.last_name_input = add_labeled_input("Фамилия автора", author['last_name'])
        self.full_name_eng_input = add_labeled_input("Полное имя (англ.)", author['full_name_eng'])
        self.email_input = add_labeled_input("Email автора", author['email'])
        self.orcid_input = add_labeled_input("ORCID автора", author['orcid'])
        self.position_input = add_labeled_input("Должность", author.get('position'))
        self.academic_degree_input = add_labeled_input("Ученая степень", author.get('academic_degree'))
        self.h_index_input = add_labeled_input("Индекс Хирша", str(author.get('h_index', '')))
        self.scopus_id_input = add_labeled_input("Scopus ID", author.get('scopus_id'))
    
        self.submit_button = QPushButton("Сохранить", self)
        self.submit_button.clicked.connect(self.submit_edit)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def submit_edit(self):
        try:
            author_obj = self.session.get(Author, self.author['author_id'])
            if not author_obj:
                QMessageBox.critical(self, "Ошибка", "Автор не найден в базе данных.")
                return

            author_obj.first_name = self.first_name_input.text()
            author_obj.mid_name = self.mid_name_input.text() or None
            author_obj.last_name = self.last_name_input.text()
            author_obj.full_name = self.full_name_input.text()
            author_obj.full_name_eng = self.full_name_eng_input.text()
            author_obj.email = self.email_input.text()
            author_obj.orcid = self.orcid_input.text()
            author_obj.position = self.position_input.text() or None
            author_obj.academic_degree = self.academic_degree_input.text() or None
            author_obj.h_index = int(self.h_index_input.text()) if self.h_index_input.text() else None
            author_obj.scopus_id = self.scopus_id_input.text() or None

            self.session.commit()
            self.accept()

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить изменения: {e}")


# def get_all_authors(session, sort_by="full_name", sort_order="asc"):
#     order = getattr(Author, sort_by)
#     if sort_order == "desc":
#         order = order.desc()  # Descending order
#     return session.query(Author).order_by(order).all()


def get_author_by_id(session, author_id):
    return session.query(Author).filter_by(author_id=author_id).first()