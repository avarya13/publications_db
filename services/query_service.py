from models.relational_models import get_session
from models.relational_models import Publication, Keyword

def find_publications_by_keyword(keyword):
    session = get_session()
    return session.query(Publication).join(Publication.keywords).filter(Keyword.keyword == keyword).all()
