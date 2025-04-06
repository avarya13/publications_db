from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship, sessionmaker, backref
from sqlalchemy.ext.declarative import declarative_base
from .mongo import MongoDB
# from pymongo import MongoClient
# import pandas as pd

Base = declarative_base()

# Роль пользователя
class Role(Base):
    __tablename__ = 'roles'
    
    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))

    users = relationship("User", back_populates="role")

# Пользователь
class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.role_id'))

    role = relationship("Role", back_populates="users")

# Пример ролей
class Permissions:
    FULL_ACCESS = "Full Access"
    READ_ONLY = "Read Only"
    COMBINED = "Combined Access"

class Journal(Base):
    __tablename__ = 'journals'
    journal_id = Column(Integer, primary_key=True)
    type = Column(String(50))
    name = Column(String(255))
    issn = Column(String(10))
    isbn = Column(String(20))

class Author(Base):
    __tablename__ = 'authors'
    author_id = Column(Integer, primary_key=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(150))
    full_name_eng = Column(String(150))
    email = Column(String(50))
    orcid = Column(String(20))

    publications = relationship("Publication", secondary="publication_authors", backref="authors_publications")  

class Institution(Base):
    __tablename__ = 'institutions'
    institution_id = Column(Integer, primary_key=True)
    name = Column(String(255))
    city = Column(String(255))
    country = Column(String(255))
    street = Column(String(255))
    house = Column(Integer)

class Publication(Base):
    __tablename__ = 'publications'
    publication_id = Column(Integer, primary_key=True)
    title = Column(String(255))
    year = Column(Integer)
    journal_id = Column(Integer, ForeignKey('journals.journal_id'))

    journal = relationship("Journal")
    authors = relationship("Author", secondary="publication_authors", backref="publications_related")  
    keywords = relationship("Keyword", secondary="publication_keywords", back_populates="publications")

    def get_metadata(self):
        """Получает метаданные из MongoDB по publication_id."""
        mongo_db = MongoDB()
        return mongo_db.get_metadata(self.publication_id) 

class Keyword(Base):
    __tablename__ = 'keywords'
    keyword_id = Column(Integer, primary_key=True)
    keyword = Column(String(50), unique=True)

    publications = relationship("Publication", secondary="publication_keywords", back_populates="keywords")  

class PublicationKeyword(Base):
    __tablename__ = 'publication_keywords'
    publication_id = Column(Integer, ForeignKey('publications.publication_id'), primary_key=True)
    keyword_id = Column(Integer, ForeignKey('keywords.keyword_id'), primary_key=True)

class PublicationAuthor(Base):
    __tablename__ = 'publication_authors'
    publication_id = Column(Integer, ForeignKey('publications.publication_id'), primary_key=True)
    author_id = Column(Integer, ForeignKey('authors.author_id'), primary_key=True)

    publication = relationship("Publication", backref="publication_authors")
    author = relationship("Author", backref="author_publications")  

class AuthorInstitution(Base):
    __tablename__ = 'author_institution'
    author_id = Column(Integer, ForeignKey('authors.author_id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.institution_id'), primary_key=True)

    author = relationship("Author", backref="author_institution")
    institution = relationship("Institution", backref="institution_authors")
