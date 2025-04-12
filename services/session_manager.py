# session_manager.py

from sqlalchemy.orm import sessionmaker
from models import User  

class SessionManager:
    def __init__(self, session: sessionmaker):
        self.session = session
        self.current_user_id = None

    def set_authenticated_user(self, user_id):
        """Устанавливаем текущего авторизованного пользователя в объекте."""
        self.current_user_id = user_id

    def get_authenticated_user_id(self):
        """Получаем ID текущего авторизованного пользователя."""
        return self.current_user_id

    def get_current_user(self):
        """Метод для получения данных о текущем пользователе из базы данных."""
        if self.current_user_id is None:
            print('get_current_user', 'None')
            return None
        user = self.session.query(User).filter(User.user_id == self.current_user_id).one_or_none()
        print('get_current_user', user)
        return user
