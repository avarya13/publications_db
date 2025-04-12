from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QHBoxLayout, QMessageBox, QWidget, QFormLayout
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from database.relational import get_session
from models.relational_models import Institution

def get_all_institutions(session, sort_by="name"):
    """Retrieve all institutions from the database, sorted by the given column."""
    return session.query(Institution).order_by(getattr(Institution, sort_by)).all()

class InstitutionDetailsDialog(QDialog):
    def __init__(self, institution):
        super().__init__()
        self.setWindowTitle("Информация об организации")

        layout = QVBoxLayout()

        def safe_label(text, value):
            return QLabel(f"{text}: {value if value else '—'}")

        layout.addWidget(safe_label("Название", institution.name))
        layout.addWidget(safe_label("Город", institution.city))
        layout.addWidget(safe_label("Страна", institution.country))
        layout.addWidget(safe_label("Улица", institution.street))
        layout.addWidget(safe_label("Дом", institution.house))

        self.setLayout(layout)

class AddInstitutionDialog(QDialog):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Добавить организацию")

        layout = QFormLayout()

        self.name_input = QLineEdit(self)
        self.city_input = QLineEdit(self)
        self.country_input = QLineEdit(self)
        self.street_input = QLineEdit(self)
        self.house_input = QLineEdit(self)

        layout.addRow("Название:", self.name_input)
        layout.addRow("Город:", self.city_input)
        layout.addRow("Страна:", self.country_input)
        layout.addRow("Улица:", self.street_input)
        layout.addRow("Дом:", self.house_input)

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

        if not name or not city or not country or not street or not house:
            QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены.")
            return

        try:
            new_institution = Institution(
                name=name, city=city, country=country, street=street, house=int(house)
            )
            self.session.add(new_institution)
            self.session.commit()
            self.accept()  # Close the dialog
        except SQLAlchemyError as e:
            self.session.rollback()
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить организацию: {str(e)}")

class EditInstitutionDialog(QDialog):
    def __init__(self, session, institution):
        super().__init__()
        self.session = session
        self.institution = institution
        self.setWindowTitle("Редактировать организацию")

        layout = QFormLayout()

        self.name_input = QLineEdit(self)
        self.city_input = QLineEdit(self)
        self.country_input = QLineEdit(self)
        self.street_input = QLineEdit(self)
        self.house_input = QLineEdit(self)

        self.name_input.setText(institution.name)
        self.city_input.setText(institution.city)
        self.country_input.setText(institution.country)
        self.street_input.setText(institution.street)
        self.house_input.setText(str(institution.house))

        layout.addRow("Название:", self.name_input)
        layout.addRow("Город:", self.city_input)
        layout.addRow("Страна:", self.country_input)
        layout.addRow("Улица:", self.street_input)
        layout.addRow("Дом:", self.house_input)

        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.save_institution)

        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def save_institution(self):
        """Saves the edited institution data to the database."""
        self.institution.name = self.name_input.text().strip()
        self.institution.city = self.city_input.text().strip()
        self.institution.country = self.country_input.text().strip()
        self.institution.street = self.street_input.text().strip()
        self.institution.house = int(self.house_input.text().strip())

        if not self.institution.name or not self.institution.city or not self.institution.country or not self.institution.street or not self.institution.house:
            QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены.")
            return

        try:
            self.session.commit()
            self.accept()  # Close the dialog
        except SQLAlchemyError as e:
            self.session.rollback()
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить изменения: {str(e)}")

class InstitutionsTab(QWidget):
    def __init__(self):
        super().__init__()

        self.session = get_session()
        self.layout = QVBoxLayout(self)

        # Строка поиска
        self.search_line_edit = QLineEdit(self)
        self.search_line_edit.setPlaceholderText("Введите название организации для поиска...")
        self.search_line_edit.textChanged.connect(self.filter_institutions)
        self.layout.addWidget(self.search_line_edit)

        # Список организаций
        self.institutions_list = QListWidget(self)
        self.institutions_list.doubleClicked.connect(self.on_institution_double_clicked)  # Connect double click to view details
        self.layout.addWidget(self.institutions_list)

        # Кнопки для добавления и редактирования организаций
        self.buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Добавить организацию", self)
        self.add_button.clicked.connect(self.add_institution)
        self.buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Редактировать организацию", self)
        self.edit_button.clicked.connect(self.edit_institution)
        self.buttons_layout.addWidget(self.edit_button)
        self.layout.addLayout(self.buttons_layout)

        # Кнопка для сортировки
        self.sort_button = QPushButton("Сортировать по имени", self)
        self.sort_button.clicked.connect(self.sort_institutions)
        self.layout.addWidget(self.sort_button)

        # Лейбл для отображения количества организаций
        self.counter_label = QLabel("Всего организаций: 0", self)
        self.layout.addWidget(self.counter_label)

        # Загружаем все организации
        self.institutions_data = []
        self.load_institutions()

    def load_institutions(self):
        """Загружает все организации из базы данных."""
        try:
            institutions = get_all_institutions(self.session)
            self.institutions_data = institutions
            self.update_institutions_list(institutions)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить организации: {e}")

    def update_institutions_list(self, institutions):
        """Обновляет список организаций."""
        self.institutions_list.clear()
        if institutions:
            for institution in institutions:
                self.institutions_list.addItem(institution.name)
        else:
            self.institutions_list.addItem("Не найдено организаций.")
        self.counter_label.setText(f"Всего организаций: {len(self.institutions_list)}")

    def filter_institutions(self):
        """Фильтрует организации по названию."""
        filter_text = self.search_line_edit.text().lower()
        if filter_text:
            filtered_institutions = [
                institution for institution in self.institutions_data
                if filter_text in (institution.name or "").lower()
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
                (institution for institution in self.institutions_data if institution.name == selected_name),
                None
            )
            if selected_institution:
                dialog = InstitutionDetailsDialog(selected_institution)
                dialog.exec()

    def add_institution(self):
        """Открывает диалог для добавления новой организации."""
        dialog = AddInstitutionDialog(self.session)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_institutions()

    def edit_institution(self):
        """Открывает диалог для редактирования выбранной организации."""
        selected_item = self.institutions_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите организацию для редактирования.")
            return

        selected_name = selected_item.text()
        selected_institution = next(
            (institution for institution in self.institutions_data if institution.name == selected_name),
            None
        )
        if selected_institution:
            dialog = EditInstitutionDialog(self.session, selected_institution)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_institutions()

    def sort_institutions(self):
        """Сортирует список организаций по алфавиту в обоих направлениях."""
        if self.institutions_data:
            self.institutions_data.sort(key=lambda x: x.name.lower(), reverse=False)  # Sort ascending
            self.update_institutions_list(self.institutions_data)
