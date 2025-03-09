from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from services.publication_service import get_authors_by_publication

class PublicationDetailsDialog(QDialog):
    def __init__(self, publication):
        super().__init__()
        self.setWindowTitle("Детали публикации")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        # Основная информация
        layout.addWidget(QLabel(f"Название: {publication.title}"))
        layout.addWidget(QLabel(f"Год: {publication.year}"))
        layout.addWidget(QLabel(f"Журнал: {publication.journal}"))
        layout.addWidget(QLabel(f"Организация: {publication.institution}"))

        # Получение авторов
        try:
            authors = get_authors_by_publication(publication.id)
            authors_text = ", ".join([author.full_name for author in authors])
        except Exception as e:
            authors_text = "Ошибка загрузки авторов"
            print(f"Ошибка: {e}")

        layout.addWidget(QLabel(f"Авторы: {authors_text}"))

        close_button = QPushButton("Закрыть", self)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)
