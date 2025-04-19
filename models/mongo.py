from pymongo import MongoClient

class MongoDB:
    def __init__(self, db_name="publications_db", collection_name="publications_metadata"):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def create_publication_metadata(
        self,
        publication_id,
        doi,
        link,
        abstract,
        citations,
        language,
        projects,
        status,
        type,
        bibliography,
        citations_wos,
        citations_rsci,
        citations_scopus,
        citations_rinz,
        citations_vak,
        patent_date
    ):
        """Функция для добавления мета-данных публикации в MongoDB"""
        metadata = {
            "publication_id": publication_id,
            "doi": doi,
            "link": link,
            "abstract": abstract,
            "citations": citations,
            "language": language,
            "projects": projects,
            "publication_status": status,
            "publication_type": type,
            "bibliography": bibliography,
            "citations_wos": citations_wos,
            "citations_rsci": citations_rsci,
            "citations_scopus": citations_scopus,
            "citations_rinz": citations_rinz,
            "citations_vak": citations_vak,
            "patent_date": patent_date
        }

        metadata_id = self.collection.insert_one(metadata).inserted_id
        return metadata_id

    def insert_metadata(self, metadata):
        """Добавляет метаданные с ID публикации."""
        self.collection.insert_one(metadata)

    def get_metadata(self, publication_id):
        """Получает метаданные по publication_id."""
        for doc in self.collection.find():
            print(doc)

        return self.collection.find_one({"publication_id": publication_id})

    def close_connection(self):
        """Закрывает соединение с MongoDB."""
        self.client.close()

    def delete_metadata(self, publication_id):
        self.collection.delete_one({"publication_id": publication_id})

