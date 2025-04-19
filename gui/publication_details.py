from services.publication_service import get_authors_by_publication
from models.mongo import MongoDB 
from PyQt6.QtWidgets import (
    QDialog, QLabel, QTextEdit, QPushButton, QVBoxLayout,
    QScrollArea, QWidget
)
from PyQt6.QtCore import Qt

class PublicationDetailsDialog(QDialog):
    def __init__(self, publication):
        super().__init__()
        self.setWindowTitle("Детали публикации")
        self.setGeometry(200, 200, 600, 700)

        # Применяем стиль
        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
                font-family: Segoe UI, sans-serif;
                background-color: #f9f7f3;
            }

            QLabel {
                font-weight: regular;
                color: #4a4a4a;
            }

            QTextEdit {
                padding: 6px;
                border: 1px solid #b8b4a8;
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 13px;
                color: #333;
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
        """)

        # Основной layout
        main_layout = QVBoxLayout(self)

        # Прокручиваемая область
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)

        def add_labeled_text(label, text):
            content_layout.addWidget(QLabel(f"<b>{label}:</b>"))
            text_label = QLabel(text)
            text_label.setWordWrap(True)
            content_layout.addWidget(text_label)

        # Основная информация
        add_labeled_text("Название", publication.get('title', '-'))
        add_labeled_text("Год", str(publication.get('year', '-')))
        add_labeled_text("Журнал", publication.get('journal', '-'))

        print('PUB', publication)

        # Извлечение ключевых слов через отношение (SQLAlchemy)
        keywords_text = ", ".join([keyword for keyword in publication['keywords']]) if publication['keywords'] else "-"
        add_labeled_text("Ключевые слова", keywords_text)

        # Авторы
        try:
            authors = get_authors_by_publication(publication['publication_id'])
            authors_text = ", ".join([author.full_name for author in authors])
        except Exception as e:
            authors_text = "Ошибка загрузки авторов"
            print(f"Ошибка: {e}")

        add_labeled_text("Авторы", authors_text)

        # Метаданные
        try:
            mongo_db = MongoDB()
            meta_data = mongo_db.get_metadata(publication['publication_id'])

            def get_display_text(field_name):
                return meta_data.get(field_name, "-")

            # Аннотация
            content_layout.addWidget(QLabel("<b>Аннотация:</b>"))
            annotation_field = QTextEdit()
            annotation_field.setPlainText(meta_data.get('abstract', "-"))
            annotation_field.setReadOnly(True)
            annotation_field.setFixedHeight(150)
            content_layout.addWidget(annotation_field)

            # Электронная библиография
            content_layout.addWidget(QLabel("<b>Электронная библиография:</b>"))
            bibliography_field = QTextEdit()
            bibliography_field.setPlainText(meta_data.get('electronic_bibliography', "-"))
            bibliography_field.setReadOnly(True)
            bibliography_field.setFixedHeight(120)
            content_layout.addWidget(bibliography_field)

            # Остальные поля
            for label, key in [
                ("Проект", "projects"),
                ("Статус публикации", "publication_status"),
                ("Тип публикации", "publication_type"),
                ("DOI", "doi"),
                ("Цитирование (WoS)", "citations_wos"),
                ("Цитирование (RSCI)", "citations_rsci"),
                ("Цитирование (Scopus)", "citations_scopus"),
                ("Цитирование (РИНЦ)", "citations_rinz"),
                ("Цитирование (ВАК)", "citations_vak"),
                ("Дата подачи патента", "patent_application_date")
            ]:
                add_labeled_text(label, get_display_text(key))

        except Exception as e:
            print(f"Ошибка загрузки метаинформации: {e}")

        # Установка прокручиваемого виджета
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Кнопка закрытия
        close_button = QPushButton("Закрыть", self)
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)