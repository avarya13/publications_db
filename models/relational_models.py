from sqlalchemy import Column, Float, Integer, String, Text, ForeignKey,  Enum as SqlEnum
from sqlalchemy.ext.declarative import declarative_base
from .mongo import MongoDB
from enum import Enum as PyEnum
from sqlalchemy.orm import relationship
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()

class UserRole(PyEnum):
    GUEST = "guest"
    AUTHOR = "author"
    ADMIN = "admin"

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SqlEnum(UserRole), default=UserRole.GUEST)

    author = relationship("Author", back_populates="user", uselist=False)

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
    publisher = Column(String(200))
    quartile = Column(String(2))
    impact_factor = Column(Float)
    website = Column(String(200))

class Author(Base):
    __tablename__ = 'authors'
    
    author_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    mid_name = Column(String(100))  
    full_name = Column(String(150))
    full_name_eng = Column(String(150))
    email = Column(String(50))
    orcid = Column(String(20))
    h_index = Column(String(10))
    scopus_id = Column(String(20))
    position = Column(String(100))  
    academic_degree = Column(String(50))  
    
    user = relationship("User", back_populates="author", uselist=False)
    publications = relationship("Publication", secondary="publication_authors", back_populates="authors")
    institutions = relationship("AuthorInstitution", back_populates="author", cascade="all, delete-orphan")

class Institution(Base):
    __tablename__ = 'institutions'
    institution_id = Column(Integer, primary_key=True)
    name = Column(String(255))
    full_name = Column(Text)  
    city = Column(String(255))
    country = Column(String(255))
    region = Column(String(100))  
    street = Column(String(255))
    house = Column(Integer)
    postal_code = Column(String(20))  
    website = Column(String(200)) 
    
    authors = relationship("AuthorInstitution", back_populates="institution", cascade="all, delete-orphan")

class Publication(Base):
    __tablename__ = 'publications'
    publication_id = Column(Integer, primary_key=True)
    title = Column(String(255))
    year = Column(Integer)
    journal_id = Column(Integer, ForeignKey('journals.journal_id'))
    # Новые поля
    volume = Column(String(10))
    issue = Column(String(10))
    pages = Column(String(20))

    journal = relationship("Journal")
    authors = relationship("Author", secondary="publication_authors", back_populates="publications")
    keywords = relationship("Keyword", secondary="publication_keywords", back_populates="publications")

    def get_metadata(self):
        mongo_db = MongoDB()
        return mongo_db.get_metadata(self.publication_id)
    
    def to_dict(self):
        return {
            "publication_id": self.publication_id,
            "title": self.title,
            "year": self.year,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "journal_id": self.journal_id,
            "journal": self.journal.name if self.journal else None,
            "authors": [author.full_name for author in self.authors],
            "keywords": [keyword.keyword for keyword in self.keywords]
        }

class Keyword(Base):
    __tablename__ = 'keywords'
    keyword_id = Column(Integer, primary_key=True)
    keyword = Column(String(50), unique=True)
    category = Column(String(50)) 

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

    author = relationship("Author", back_populates="institutions")
    institution = relationship("Institution", back_populates="authors")