import psycopg2
from collections import namedtuple
from database.relational import get_session
from models.relational_models import Publication
from services.user_service import get_user_role
from models.relational_models import Permissions
from models import Journal, Author, Institution, Publication, PublicationAuthor

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


import psycopg2

Publication = namedtuple("Publication", ["id", "title", "journal", "year", "volume", "doi", "author", "institution"])

def get_all_publications(title=None, author=None, journal=None, institution=None):
    # Подключение к базе данных
    conn = psycopg2.connect(
        dbname="publications_db", 
        user="postgres", 
        password="per33sik", 
        host="localhost", 
        port="5432"
    )
    
    cur = conn.cursor()
    
    # Базовый SQL-запрос
    query = """
        SELECT p.publication_id, p.title, j.name AS journal_name, p.year, p.volume, p.doi, 
               a.full_name AS author_name, i.name AS institution_name
        FROM publications p
        LEFT JOIN publication_authors pa ON p.publication_id = pa.publication_id
        LEFT JOIN authors a ON pa.author_id = a.author_id
        LEFT JOIN journals j ON p.journal_id = j.journal_id
        LEFT JOIN institutions i ON a.author_id = i.institution_id
        WHERE TRUE
    """
    
    filters = []

    # Фильтры по подстрокам
    if title:
        query += " AND p.title ILIKE %s"
        filters.append(f"%{title}%")
    if author:
        query += " AND a.full_name ILIKE %s"
        filters.append(f"%{author}%")
    if journal:
        query += " AND j.name ILIKE %s"
        filters.append(f"%{journal}%")
    if institution:
        query += " AND i.name ILIKE %s"
        filters.append(f"%{institution}%")

    # Выполнение запроса с фильтрами
    cur.execute(query, filters)
    
    # Получаем данные и преобразуем их в список экземпляров Publication
    publications = [Publication(*row) for row in cur.fetchall()]
    
    # Закрытие соединения
    cur.close()
    conn.close()

    return publications


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

def create_publication(session, title, year, journal_id, authors, institutions):
    new_publication = Publication(title=title, year=year, journal_id=journal_id)
    session.add(new_publication)
    session.commit()

    # Добавляем авторов и институты
    for author_name in authors:
        author = session.query(Author).filter_by(full_name=author_name).first()
        if author:
            new_publication.authors.append(author)

    for inst_name in institutions:
        institution = session.query(Institution).filter_by(name=inst_name).first()
        if institution:
            new_publication.institutions.append(institution)

    session.commit()

def get_authors_by_publication(publication_id):
    session = get_session()
    try:
        authors = session.query(Author).join(PublicationAuthor).filter(PublicationAuthor.publication_id == publication_id).all()
        return authors
    finally:
        session.close()
