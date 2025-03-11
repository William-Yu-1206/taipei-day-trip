import mysql.connector
import json
import re

# connect mysql
con = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456789",
    database="day_trip"
)

# import data from .json file
with open("data/taipei-attractions.json", mode="r") as response:
    data = json.load(response)
    data = data["result"]["results"]

# store data into db_day_trip
with con.cursor() as cursor:
    selected_columns = ["name", "CAT", "description", "address", "direction", "MRT", "latitude", "longitude", "file"]
    pattern = r'https://[^h]*(?:\.(?:jpg|JPG|png|PNG))'
    for spot in data:
        # clean data for images
        images = spot["file"]
        urls = re.findall(pattern, images)
        result = ",".join(urls)
        spot["file"] = result
        # store data into table_attraction
        values = [spot[column] for column in selected_columns]
        query = "insert into attraction(name, category, description, address, transport, mrt, lat, lng, images) values(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, values)
        con.commit()
