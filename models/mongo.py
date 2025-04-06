from pymongo import MongoClient

class MongoDB:
    def __init__(self, db_name="publications_db", collection_name="publications_metadata"):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_metadata(self, metadata):
        """Добавляет метаданные с ID публикации."""
        self.collection.insert_one(metadata)

    def get_metadata(self, publication_id):
        """Получает метаданные по publication_id."""
        return self.collection.find_one({"publication_id": publication_id})

    def close_connection(self):
        """Закрывает соединение с MongoDB."""
        self.client.close()

