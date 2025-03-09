from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from database.relational import SessionLocal
from models.relational_models import User, Role
from werkzeug.security import generate_password_hash, check_password_hash

# Настройка подключения
DATABASE_URL = "postgresql+psycopg2://username:password@localhost/publications_db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def create_user(username, password, role_name):
    hashed_password = generate_password_hash(password)
    
    # Находим роль по имени
    role = session.query(Role).filter_by(role_name=role_name).first()

    if role:
        user = User(username=username, password_hash=hashed_password, role=role)
        session.add(user)
        session.commit()
    else:
        raise ValueError(f"Роль {role_name} не существует")

def check_user_credentials(username, password):
    user = session.query(User).filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        return user
    return None

# Получение текущего пользователя (имитация для примера)
def get_current_user():
    # Это просто пример, вы должны сделать реальную аутентификацию
    # Например, по ID или сессионному идентификатору
    with SessionLocal() as session:
        user = session.query(User).filter(User.username == "some_user").first()
    return user

# Проверка роли пользователя
def get_user_role():
    user = get_current_user()
    if user:
        return user.role
    return None

def register_user(username: str, password: str) -> bool:
    session = Session()
    # Проверяем, существует ли уже пользователь
    if session.query(User).filter_by(username=username).first():
        return False  # Пользователь уже существует

    hashed_password = generate_password_hash(password)  # Хеширование пароля
    new_user = User(username=username, password_hash=hashed_password)
    session.add(new_user)
    session.commit()
    session.close()
    return True

def login_user(username: str, password: str) -> bool:
    session = Session()
    user = session.query(User).filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session.close()
        return True  # Успешный вход
    session.close()
    return False  # Неверные имя пользователя или пароль

