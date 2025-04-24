from .main_window import MainWindow
from .add_publication import AddPublicationDialog
# from .add_user import AddUserDialog
from .login import LoginDialog  # Импорт окна входа
from .register import RegisterDialog  # Импорт окна регистрации
from .edit_profile import EditProfileDialog
from .assign_author import AssignAuthorDialog

__all__ = ["MainWindow", "AddPublicationDialog", "AddUserDialog", "LoginDialog", 
           "RegisterDialog", "EditProfileDialog", "AssignAuthorDialog"]
