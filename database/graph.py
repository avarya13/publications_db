# from neo4j import GraphDatabase

# uri = "bolt://localhost:7687"
# driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))


# def get_graph_session():
#     """Создаёт и возвращает сессию для работы с Neo4j."""
#     return driver.session()

# def create_author(tx, name):
#     tx.run("MERGE (a:Author {name: $name})", name=name)

# def create_coauthorship(tx, author1, author2):
#     tx.run("""
#         MATCH (a1:Author {name: $author1}), (a2:Author {name: $author2})
#         MERGE (a1)-[:COAUTHORED]->(a2)
#     """, author1=author1, author2=author2)

# with driver.session() as session:
#     session.write_transaction(create_author, "Alice")
#     session.write_transaction(create_author, "Bob")
#     session.write_transaction(create_coauthorship, "Alice", "Bob")
