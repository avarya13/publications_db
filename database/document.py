from pymongo import MongoClient

mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["publications_mongo"]


from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.publications_db
publications = db.publications

# Поиск публикаций по тегу
def search_publications_by_tag(tag_name):
    return publications.find({"tags": tag_name})




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
