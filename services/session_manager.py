# session_manager.py

from sqlalchemy.orm import sessionmaker
from models import User, UserRole

class SessionManager:
    def __init__(self, session: sessionmaker):
        self.session = session
        self.current_user_id = None
        self.user_role = None

    def set_authenticated_user(self, user_id):
        """Устанавливаем текущего авторизованного пользователя в объекте."""
        self.current_user_id = user_id

    def get_authenticated_user_id(self):
        """Получаем ID текущего авторизованного пользователя."""
        return self.current_user_id

    def get_current_user(self):
        """Метод для получения данных о текущем пользователе из базы данных."""
        if self.current_user_id is None:
            print('Текущий пользователь:', 'None')
            return None
        user = self.session.query(User).filter(User.user_id == self.current_user_id).one_or_none()
        print('Текущий пользователь:', user, user.role)
        return user
    
    def set_user_role(self, role: UserRole):
        self.user_role = role

    def get_user_role(self):
        return self.user_role
        # user = self.get_current_user()
        # print('Текущий пользователь 1:', user, user.role)
        # # if user:
        # return user.role  
        # # return None

