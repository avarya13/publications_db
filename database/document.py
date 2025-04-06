from pymongo import MongoClient

# Подключение к MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["publications_db"]  # Название базы данных
metadata_collection = mongo_db["publication_metadata"]  # Коллекция мета-данных

def create_publication_metadata(session, publication_id, doi, link, keywords, abstract, citations, language):
    """ Функция для добавления мета-данных публикации в MongoDB """
    metadata = {
        "publication_id": publication_id,  # Ссылка на публикацию в основной базе
        "doi": doi,
        "link": link,
        "keywords": keywords,
        "abstract": abstract,
        "citations": citations
    }
    metadata_id = metadata_collection.insert_one(metadata).inserted_id
    return metadata_id

def get_publication_metadata(session, publication_id):
    """ Получить мета-данные публикации по идентификатору """
    metadata = metadata_collection.find_one({"publication_id": publication_id})
    return metadata




# # Добавляем публикацию
# mongo_db.publication_fulltexts.insert_one({
#     "publication_id": 1,
#     "title": "Deep Learning in Medical Imaging",
#     "full_text": "Полный текст статьи..."
# })

# # Добавляем комментарий
# mongo_db.comments.insert_one({
#     "publication_id": 1,
#     "user": "Alice",
#     "comment": "Отличная статья!",
#     "date": "2024-03-01"
# })
