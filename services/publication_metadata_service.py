from pymongo import MongoClient

class MongoDB:
    def __init__(self, db_name="publications_db", collection_name="publications_metadata"):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_metadata(self, metadata):
        """Добавляет одну запись в коллекцию."""
        self.collection.insert_one(metadata)

    def get_metadata(self, doi):
        """Получает метаданные по DOI."""
        return self.collection.find_one({"doi": doi})

    def get_all_metadata(self):
        """Получает все метаданные из коллекции."""
        return list(self.collection.find())

    def close_connection(self):
        """Закрывает соединение с MongoDB."""
        self.client.close()
