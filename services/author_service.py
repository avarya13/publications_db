from database.relational import get_session
from models.relational_models import Author
# , Coauthorship

def create_author(first_name, last_name, affiliation):
    session = get_session()
    author = Author(first_name=first_name, last_name=last_name, affiliation=affiliation)
    session.add(author)
    session.commit()
    return author.author_id

# def create_coauthorship(author_id1, author_id2):
#     session = get_session()
#     coauthorship = Coauthorship(author1_id=author_id1, author2_id=author_id2)
#     session.add(coauthorship)
#     session.commit()
