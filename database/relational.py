import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.relational_models import Base

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql+psycopg2://postgres:per33sik@localhost/publications_db"

try:
    engine = create_engine(DATABASE_URL)
    logger.info("Соединение с базой данных установлено.")
except Exception as e:
    logger.error(f"Ошибка при подключении: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Создает таблицы, если их нет"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Таблицы базы данных созданы.")
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")

def get_session():
    """Создает сессию для работы с БД"""
    try:
        session = SessionLocal()
        logger.info("Сессия успешно создана.")
        return session
    except Exception as e:
        logger.error(f"Ошибка при создании сессии: {e}")
        raise
