import os
from dotenv import load_dotenv
from mysql.connector import pooling

class db:
    def connectPool():
        load_dotenv()
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="day_trip_pool",
            pool_size=5,
            host="localhost",
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return connection_pool

