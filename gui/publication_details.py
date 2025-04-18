from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
from services.publication_service import get_authors_by_publication
from models.mongo import MongoDB 

class PublicationDetailsDialog(QDialog):
    def __init__(self, publication):
        super().__init__()
        self.setWindowTitle("Детали публикации")
        self.setGeometry(200, 200, 400, 500)  

        layout = QVBoxLayout()

        # Основная информация
        layout.addWidget(QLabel(f"Название: {publication['title']}"))
        layout.addWidget(QLabel(f"Год: {publication['year']}"))
        layout.addWidget(QLabel(f"Журнал: {publication['journal']}"))

        # Получение авторов
        try:
            authors = get_authors_by_publication(publication['publication_id'])
            authors_text = ", ".join([author.full_name for author in authors])
        except Exception as e:
            authors_text = "Ошибка загрузки авторов"
            print(f"Ошибка: {e}")

        layout.addWidget(QLabel(f"Авторы: {authors_text}"))

        try:
            mongo_db = MongoDB()
            meta_data = mongo_db.get_metadata(publication['publication_id'])

            print("META", meta_data)
            
            def get_display_text(field_name):
                return meta_data.get(field_name, "-")
            
            annotation_text = meta_data.get('abstract', "-")
            bibliography_text = meta_data.get('electronic_bibliography', "-")
            
            annotation_field = QTextEdit()
            annotation_field.setPlainText(annotation_text)
            annotation_field.setReadOnly(True)  
            layout.addWidget(QLabel(f"Аннотация:"))
            layout.addWidget(annotation_field)

            # Библиография
            bibliography_field = QTextEdit()
            bibliography_field.setPlainText(bibliography_text)
            bibliography_field.setReadOnly(True) 
            layout.addWidget(QLabel(f"Электронная библиография:"))
            layout.addWidget(bibliography_field)

            # Остальные поля с метаданными
            layout.addWidget(QLabel(f"Проект: {get_display_text('projects')}"))
            layout.addWidget(QLabel(f"Статус публикации: {get_display_text('publication_status')}"))
            layout.addWidget(QLabel(f"Тип публикации: {get_display_text('publication_type')}"))
            layout.addWidget(QLabel(f"DOI: {get_display_text('doi')}"))
            layout.addWidget(QLabel(f"Цитирование (WoS): {get_display_text('citations_wos')}"))
            layout.addWidget(QLabel(f"Цитирование (RSCI): {get_display_text('citations_rsci')}"))
            layout.addWidget(QLabel(f"Цитирование (Scopus): {get_display_text('citations_scopus')}"))
            layout.addWidget(QLabel(f"Цитирование (РИНЦ): {get_display_text('citations_rinz')}"))
            layout.addWidget(QLabel(f"Цитирование (ВАК): {get_display_text('citations_vak')}"))
            layout.addWidget(QLabel(f"Дата подачи патента: {get_display_text('patent_application_date')}"))
            
        except Exception as e:
            print(f"Ошибка загрузки метаинформации: {e}")

        close_button = QPushButton("Закрыть", self)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)
