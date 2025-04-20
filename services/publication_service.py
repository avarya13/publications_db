from database.relational import get_session
from models.relational_models import Publication
from services.user_service import get_user_role
from models.relational_models import Permissions
from models import Journal, Author, Institution, Publication, PublicationAuthor, AuthorInstitution, Keyword
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.mongo import MongoDB
from models.redis_client import redis_client
from sqlalchemy.orm import joinedload
import json
import hashlib


def make_cache_key(**kwargs):
    key_base = json.dumps(kwargs, sort_keys=True)
    return "publications:" + hashlib.md5(key_base.encode()).hexdigest()

def get_all_publications_cached(session, **filters):
    cache_key = make_cache_key(**filters)

    cached = redis_client.get(cache_key)
    if cached:
        print("Publications were loaded from Redis cache")
        return json.loads(cached)  

    publications = get_all_publications(session, **filters)
    publications_data = [p.to_dict() for p in publications]

    redis_client.set(cache_key, json.dumps(publications_data), ex=3600)  
    return publications_data

def clear_publication_cache():
    print('Очистка кэша после удаления')
    keys = redis_client.keys("publications:*")
    for key in keys:
        redis_client.delete(key)  

def can_user_create_publication(user):
    role = get_user_role(user)
    if role == Permissions.FULL_ACCESS:
        return True
    if role == Permissions.COMBINED:
        return True
    return False

def can_user_view_publication(user):
    role = get_user_role(user)
    if role == Permissions.FULL_ACCESS:
        return True
    if role == Permissions.READ_ONLY:
        return True
    return False


# def get_all_publications():
#     session = get_session()
#     publications = session.query(Publication).all()
#     session.close()
#     return publications



def get_all_publications(session, title=None, author=None, journal=None, keyword=None): #institution=None, 

    try:
        query = session.query(Publication).options(
            joinedload(Publication.journal),
            joinedload(Publication.authors),
            joinedload(Publication.keywords)
        )

        if title:
            query = query.filter(Publication.title.ilike(f"%{title}%"))

        if journal:
            query = query.join(Publication.journal).filter(Journal.name.ilike(f"%{journal}%"))

        if author:
            query = query.join(Publication.authors).filter(Author.full_name.ilike(f"%{author}%"))

        if keyword:
            query = query.join(Publication.keywords).filter(Keyword.keyword.ilike(f"%{keyword}%"))

        # if institution:
        #     # Через авторов → связку author_institution → institution
        #     query = query.join(Publication.authors).join(Author.institutions).filter(Institution.name.ilike(f"%{institution}%"))

        query = query.distinct().order_by(Publication.publication_id)

        return query.all()

    finally:
        session.close()

def create_publication(title, year):
    session = get_session()
    new_pub = Publication(title=title, year=year)
    session.add(new_pub)
    session.commit()
    session.close()

def get_journals(session):
    return session.query(Journal).all()

def get_authors(session):
    return session.query(Author).all()

def get_institutions(session):
    return session.query(Institution).all()

def create_publication(session, title, year, journal_id, author_ids, keywords):
    # Создаем новую публикацию
    publication = Publication(
        title=title,
        year=year,
        journal_id=journal_id,
    )
    session.add(publication)
    session.commit()  # Сохраняем публикацию, чтобы получить её ID

    # Привязываем авторов к публикации
    for author_id in author_ids:
        author = session.query(Author).filter(Author.author_id == author_id).one()
        publication.authors.append(author)

    # Привязываем ключевые слова к публикации
    existing_keywords = {kw.keyword for kw in publication.keywords}
    for keyword_text in keywords.split(','):
        keyword_text = keyword_text.strip()
        if keyword_text in existing_keywords:
            continue  # Уже привязано

        keyword = session.query(Keyword).filter(Keyword.keyword == keyword_text).first()
        if not keyword:
            keyword = Keyword(keyword=keyword_text)
            session.add(keyword)
            session.flush()  # Получаем ID без commit

        if keyword not in publication.keywords:
            publication.keywords.append(keyword)

    session.commit()  # Сохраняем все изменения

    return publication.publication_id

def get_authors_by_publication(publication_id):
    session = get_session()
    try:
        authors = session.query(Author).join(PublicationAuthor).filter(PublicationAuthor.publication_id == publication_id).all()
        return authors
    finally:
        session.close()

def get_publication_by_id(session, publication_id):
    print(f"get_publication_by_id() получил ID: {publication_id}")  
    if not isinstance(publication_id, int):
        raise ValueError(f"publication_id должен быть int, а не {type(publication_id)}")
    
    if not hasattr(session, "query"):
        raise TypeError(f"session не является объектом SQLAlchemy Session, а {type(session)}")
    
    print(Publication)
    print(isinstance(Publication, type))
    print(hasattr(Publication, "__tablename__"))
    print(hasattr(Publication, "publication_id"))
    print(session.bind) 
    print(session.is_active)  
    
    result = session.query(Publication).filter(Publication.publication_id == publication_id).first()
    if result is None:
        print(f"Публикация с ID {publication_id} не найдена.")
    return result

def update_publication(session: Session, publication_id: int, title: str, year: int, journal_id: int, authors: list, institutions: list, doi: str, link: str, keywords: list, abstract: str, citations: str, language: str):
    """Обновление публикации по ID"""
    # Получаем публикацию по ID
    publication = session.query(Publication).filter(Publication.publication_id == publication_id).first()
    
    if not publication:
        raise ValueError(f"Публикация с ID {publication_id} не найдена.")
    
    # Обновляем поля публикации
    publication.title = title
    publication.year = year
    publication.journal_id = journal_id

    # Обновляем связи с авторами и институтами в реляционной БД
    current_author_ids = [author.author_id for author in publication.authors]
    current_institution_ids = [inst.institution_id for inst in publication.institutions]

    # Удаляем авторов и институты, которые больше не выбраны
    for author_id in current_author_ids:
        if author_id not in authors:  # authors should be a list of author_ids
            publication_authors_institution = session.query(AuthorInstitution).filter(
                and_(
                    AuthorInstitution.publication_id == publication_id,
                    AuthorInstitution.author_id == author_id
                )
            ).first()
            if publication_authors_institution:
                session.delete(publication_authors_institution)

    # Добавляем новых авторов и их институты
    for author_id in authors:  # Ensure authors is a list of author_ids
        # Проверяем, что автор еще не связан с публикацией
        if author_id not in current_author_ids:
            # Создаем запись о связи автора с институтом
            for institution_id in institutions:  # institutions should be a list of institution_ids
                if institution_id not in current_institution_ids:
                    author_institution = AuthorInstitution(publication_id=publication_id, author_id=author_id, institution_id=institution_id)
                    session.add(author_institution)

    # Обновляем метаинформацию в MongoDB
    try:
        mongo_db = MongoDB()
        meta_data = mongo_db.get_metadata(publication_id)
        
        # Обновление метаинформации в MongoDB
        if meta_data:
            meta_data['abstract'] = abstract
            meta_data['projects'] = meta_data.get('projects', "-")  # Проверка, если проекты отсутствуют
            meta_data['publication_status'] = meta_data.get('publication_status', "-")
            meta_data['publication_type'] = meta_data.get('publication_type', "-")
            meta_data['doi'] = doi if doi else meta_data.get('doi', "-")  # Обновление DOI
            meta_data['electronic_bibliography'] = meta_data.get('electronic_bibliography', "-")
            meta_data['citations_wos'] = meta_data.get('citations_wos', "-")
            meta_data['citations_rsci'] = meta_data.get('citations_rsci', "-")
            meta_data['citations_scopus'] = meta_data.get('citations_scopus', "-")
            meta_data['citations_rinz'] = meta_data.get('citations_rinz', "-")
            meta_data['citations_vak'] = meta_data.get('citations_vak', "-")
            meta_data['patent_application_date'] = meta_data.get('patent_application_date', "-")
            
            # Обновляем метаинформацию в MongoDB
            mongo_db.collection.update_one(
                {"publication_id": publication_id},
                {"$set": meta_data},
                upsert=True  # Если документа с таким publication_id нет, будет создан новый
            )
    except Exception as e:
        print(f"Ошибка обновления метаинформации в MongoDB: {e}")

    # Сохраняем изменения в реляционной базе данных
    session.commit()

def get_publication_meta(publication_id):
    collection = MongoDB.get_metadata('publications_meta')  
    meta_data = collection.find_one({'publication_id': publication_id})
    return meta_data if meta_data else {}


