from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QHBoxLayout, QMessageBox, QWidget, QFormLayout
from PyQt6.QtGui import QIntValidator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from database.relational import get_session
from models.relational_models import Institution, UserRole
from models.redis_client import redis_client
import json

def get_all_institutions(session, sort_by="name", descending=False):
    key = f"institutions:{sort_by}:{'desc' if descending else 'asc'}"
    cached = redis_client.get(key)
    if cached:
        print("Institutions were loaded from Redis cache")
        return json.loads(cached)

    order = getattr(Institution, sort_by)
    if descending:
        order = order.desc()
    institutions = session.query(Institution).order_by(order).all()

    data = [{
        "institution_id": i.institution_id,
        "name": i.name,
        "country": i.country,
        "city": i.city,
        "street": i.street,
        "house": i.house,
        "full_name": i.full_name,
        "region": i.region,
        "postal_code": i.postal_code,
        "website": i.website
    } for i in institutions]
    
    redis_client.setex(key, 300, json.dumps(data))  
    return data

# def get_all_institutions(session, sort_by="name"):
#     """Retrieve all institutions from the database, sorted by the given column."""
#     return session.query(Institution).order_by(getattr(Institution, sort_by)).all()

class InstitutionDetailsDialog(QDialog):
    def __init__(self, institution):
        super().__init__()
        self.setWindowTitle("Информация об организации")
        self.setGeometry(100, 100, 800, 200)

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

        def safe_label(text, value):
            return QLabel(f"{text}: {value if value else '—'}")

        layout.addWidget(safe_label("Полное название", institution.get('full_name')))
        layout.addWidget(safe_label("Сокращенное название", institution['name']))
        layout.addWidget(safe_label("Страна", institution['country']))
        layout.addWidget(safe_label("Регион", institution.get('region')))
        layout.addWidget(safe_label("Город", institution['city']))
        layout.addWidget(safe_label("Улица", institution['street']))
        layout.addWidget(safe_label("Дом", institution['house']))
        layout.addWidget(safe_label("Почтовый индекс", institution.get('postal_code')))
        layout.addWidget(safe_label("Сайт", institution.get('website')))
        self.setLayout(layout)

class AddInstitutionDialog(QDialog):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Добавить организацию")
        self.setGeometry(100, 100, 800, 200)

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

        layout = QFormLayout()

        self.full_name_input = QLineEdit(self)
        self.name_input = QLineEdit(self)
        self.country_input = QLineEdit(self)
        self.region_input = QLineEdit(self)
        self.city_input = QLineEdit(self)
        self.street_input = QLineEdit(self)
        self.house_input = QLineEdit(self)
        self.house_input.setValidator(QIntValidator(1, 1000))
        self.postal_code_input = QLineEdit(self)
        self.website_input = QLineEdit(self)

        layout.addRow("Полное название:", self.full_name_input)
        layout.addRow("Сокращенное название:", self.name_input)
        layout.addRow("Страна:", self.country_input)        
        layout.addRow("Регион:", self.region_input)
        layout.addRow("Город:", self.city_input)
        layout.addRow("Улица:", self.street_input)
        layout.addRow("Дом:", self.house_input)
        layout.addRow("Почтовый индекс:", self.postal_code_input)
        layout.addRow("Сайт:", self.website_input)

        self.add_button = QPushButton("Добавить", self)
        self.add_button.clicked.connect(self.add_institution)

        layout.addWidget(self.add_button)
        self.setLayout(layout)

    def add_institution(self):
        """Adds a new institution to the database."""
        name = self.name_input.text().strip()
        city = self.city_input.text().strip()
        country = self.country_input.text().strip()
        street = self.street_input.text().strip()
        house = self.house_input.text().strip()
        full_name = self.full_name_input.text().strip()
        region = self.region_input.text().strip()
        postal_code = self.postal_code_input.text().strip()
        website = self.website_input.text().strip()

        if not name or not city or not country or not street or not house:
            QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены.")
            return

        try:
            new_institution = Institution(
                name=name,
                full_name=full_name,
                city=city,
                country=country,
                region=region,
                street=street,
                house=int(house),
                postal_code=postal_code,
                website=website
            )
            self.session.add(new_institution)
            self.session.commit()
            self.accept()  
        except SQLAlchemyError as e:
            self.session.rollback()
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить организацию: {str(e)}")

class EditInstitutionDialog(QDialog):
    def __init__(self, session, institution):
        super().__init__()
        self.session = session
        self.institution = institution
        self.setWindowTitle("Редактировать организацию")
        self.setGeometry(100, 100, 800, 200)

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

        layout = QFormLayout()

        self.full_name_input = QLineEdit(self)
        self.name_input = QLineEdit(self)
        self.country_input = QLineEdit(self)
        self.region_input = QLineEdit(self)
        self.city_input = QLineEdit(self)
        self.street_input = QLineEdit(self)
        self.house_input = QLineEdit(self)
        self.house_input.setValidator(QIntValidator(1, 1000))
        self.postal_code_input = QLineEdit(self)
        self.website_input = QLineEdit(self)

        self.name_input.setText(institution['name'])
        self.country_input.setText(institution['country'])
        self.city_input.setText(institution['city'])
        self.street_input.setText(institution['street'])
        self.house_input.setText(str(institution['house']))
        self.full_name_input.setText(institution.get('full_name', ''))
        self.region_input.setText(institution.get('region', ''))
        self.postal_code_input.setText(institution.get('postal_code', ''))
        self.website_input.setText(institution.get('website', ''))

        layout.addRow("Полное название:", self.full_name_input)
        layout.addRow("Сокращенное название:", self.name_input)
        layout.addRow("Страна:", self.country_input)
        layout.addRow("Регион:", self.region_input)
        layout.addRow("Город:", self.city_input)
        layout.addRow("Улица:", self.street_input)
        layout.addRow("Дом:", self.house_input)
        layout.addRow("Почтовый индекс:", self.postal_code_input)
        layout.addRow("Сайт:", self.website_input)

        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.save_institution)

        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def save_institution(self):
        """Saves the edited institution data to the database."""

        name = self.name_input.text().strip()
        city = self.city_input.text().strip()
        country = self.country_input.text().strip()
        street = self.street_input.text().strip()
        house_text = self.house_input.text().strip()
        full_name = self.full_name_input.text().strip()
        region = self.region_input.text().strip()
        postal_code = self.postal_code_input.text().strip()
        website = self.website_input.text().strip()

        if not name or not city or not country or not street or not house_text:
            QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены.")
            return

        try:
            house = int(house_text)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Номер дома должен быть числом.")
            return

        try:
            # Найдём ORM-объект по ID
            institution_obj = self.session.get(Institution, self.institution['institution_id'])
            if not institution_obj:
                QMessageBox.critical(self, "Ошибка", "Учреждение не найдено в базе данных.")
                return

            # Обновим поля ORM-объекта
            institution_obj.name = name
            institution_obj.city = city
            institution_obj.country = country
            institution_obj.street = street
            institution_obj.house = house
            institution_obj.full_name = full_name or None
            institution_obj.region = region or None
            institution_obj.postal_code = postal_code or None
            institution_obj.website = website or None

            # Сохраним изменения
            self.session.commit()
            self.accept()

        except SQLAlchemyError as e:
            self.session.rollback()
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить изменения: {str(e)}")

class InstitutionsTab(QWidget):
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
                font-size: 13px;
                color: #4a4a4a;
            }
        """)

        # Строка поиска
        self.search_line_edit = QLineEdit(self)
        self.search_line_edit.setPlaceholderText("Введите название организации для поиска...")
        self.search_line_edit.textChanged.connect(self.filter_institutions)
        self.layout.addWidget(self.search_line_edit)

        # Список организаций
        self.institutions_list = QListWidget(self)
        self.institutions_list.doubleClicked.connect(self.on_institution_double_clicked)  
        self.layout.addWidget(self.institutions_list)

        # self.sort_button = QPushButton("Сортировать по имени", self)
        # self.sort_button.clicked.connect(self.sort_institutions)
        # self.layout.addWidget(self.sort_button)

        # Кнопки для добавления и редактирования организаций
        self.buttons_layout = QHBoxLayout()

        # Кнопка для сортировки
        self.sort_button = QPushButton("Сортировать по алфавиту (по убыванию)", self)
        self.sort_button.clicked.connect(self.toggle_sort_order)
        self.buttons_layout.addWidget(self.sort_button)

        self.add_button = QPushButton("Добавить организацию", self)
        self.add_button.clicked.connect(self.add_institution)
        self.buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Редактировать организацию", self)
        self.edit_button.clicked.connect(self.edit_institution)
        self.buttons_layout.addWidget(self.edit_button)
        self.layout.addLayout(self.buttons_layout)

        self.delete_button = QPushButton("Удалить организацию", self)
        self.delete_button.clicked.connect(self.delete_institution)
        self.buttons_layout.addWidget(self.delete_button)

        # Лейбл для отображения количества организаций
        self.counter_label = QLabel("Всего организаций: 0", self)
        self.layout.addWidget(self.counter_label)

        # Загружаем все организации
        self.institutions_data = []
        self.load_institutions()
        
        self.session_manager = session_manager    
        # self.role = self.session_manager.get_user_role()
        self.configure_ui_for_role()  

    def configure_ui_for_role(self):
        """Конфигурирует элементы интерфейса в зависимости от роли пользователя"""
        self.role = self.session_manager.get_user_role()
        if self.role == UserRole.GUEST:
            # Ограниченные права для гостей
            self.delete_button.setEnabled(False)
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
        elif self.role == UserRole.AUTHOR:
            # Права автора
            self.delete_button.setEnabled(False)
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
        elif self.role == UserRole.ADMIN:
            # Права администратора
            self.delete_button.setEnabled(True)
            self.add_button.setEnabled(True)
            self.edit_button.setEnabled(True)
        else:
            # По умолчанию
            self.delete_button.setEnabled(False)
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)

    def load_institutions(self, descending=False):
        """Загружает все организации из базы данных."""
        try:
            institutions = get_all_institutions(self.session, descending=descending)
            self.institutions_data = institutions
            self.update_institutions_list(institutions)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить организации: {e}")

    def toggle_sort_order(self):
        """Toggles sorting order between ascending and descending."""
        if self.sort_button.text() == "Сортировать по алфавиту (по убыванию)":
            self.sort_button.setText("Сортировать по алфавиту (по возрастанию)")
            self.load_institutions(descending=True)
        else:
            self.sort_button.setText("Сортировать по алфавиту (по убыванию)")
            self.load_institutions(descending=False)

    def update_institutions_list(self, institutions):
        """Обновляет список организаций."""
        self.institutions_list.clear()
        if institutions:
            for institution in institutions:
                self.institutions_list.addItem(institution['name'])
        else:
            self.institutions_list.addItem("Не найдено организаций.")
        self.counter_label.setText(f"Всего организаций: {len(self.institutions_list)}")

    def filter_institutions(self):
        """Фильтрует организации по названию."""
        filter_text = self.search_line_edit.text().lower()
        if filter_text:
            filtered_institutions = [
                institution for institution in self.institutions_data
                if filter_text in (institution['name'] or "").lower()
            ]
            self.update_institutions_list(filtered_institutions)
        else:
            self.update_institutions_list(self.institutions_data)

    def on_institution_double_clicked(self):
        """Открывает окно с информацией о выбранной организации при двойном клике."""
        selected_item = self.institutions_list.currentItem()
        if selected_item:
            selected_name = selected_item.text()
            selected_institution = next(
                (institution for institution in self.institutions_data if institution['name'] == selected_name),
                None
            )
            if selected_institution:
                dialog = InstitutionDetailsDialog(selected_institution)
                dialog.exec()

    def add_institution(self):
        """Открывает диалог для добавления новой организации."""
        dialog = AddInstitutionDialog(self.session)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.clear_institution_cache()
            self.load_institutions()

    def edit_institution(self):
        """Открывает диалог для редактирования выбранной организации."""
        selected_item = self.institutions_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите организацию для редактирования.")
            return

        selected_name = selected_item.text()
        selected_institution = next(
            (institution for institution in self.institutions_data if institution['name'] == selected_name),
            None
        )
        if selected_institution:
            dialog = EditInstitutionDialog(self.session, selected_institution)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.clear_institution_cache() 
                self.load_institutions()
    
    def clear_institution_cache(self):
        print('Очистка кэша после удаления')
        keys = redis_client.keys("institutions:*")
        for key in keys:
            redis_client.delete(key)

    def sort_institutions(self):
        """Сортирует список организаций по алфавиту в обоих направлениях."""
        if self.institutions_data:
            self.institutions_data.sort(key=lambda x: x['name'].lower(), reverse=False)  # Sort ascending
            self.update_institutions_list(self.institutions_data)

    def delete_institution(self):
        selected_item = self.institutions_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите организацию для удаления.")
            return

        selected_name = selected_item.text()
        selected_institution = next(
            (institution for institution in self.institutions_data if institution['name'] == selected_name),
            None
        )
        if not selected_institution:
            QMessageBox.warning(self, "Ошибка", "Не удалось найти организацию в списке.")
            return

        reply = QMessageBox.question(self, "Подтверждение удаления",
                                    f"Вы уверены, что хотите удалить организацию '{selected_name}'?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                institution_obj = self.session.query(Institution).filter_by(institution_id=selected_institution['institution_id']).first()
                if institution_obj:
                    self.session.delete(institution_obj)
                    self.session.commit()
                    self.clear_institution_cache()
                    QMessageBox.information(self, "Успешно", "Организация удалена.")
                    self.load_institutions()
                else:
                    QMessageBox.warning(self, "Ошибка", "Организация не найдена в базе данных.")
            except SQLAlchemyError as e:
                self.session.rollback()
                QMessageBox.warning(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
