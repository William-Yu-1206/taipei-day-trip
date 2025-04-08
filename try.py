from dbconf import db

connection_pool = db.connectPool()
connection = db.get_db_connection(connection_pool)
print(connection_pool)
print(connection)