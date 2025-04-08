from typing import Literal
from pydantic import BaseModel, HttpUrl
from datetime import date
import datetime

class AttractionBody(BaseModel):
    attractionId: int
    date: date
    time: str
    price: int

class BookingAttraction(BaseModel):
    id: int
    name: str
    address: str
    image: HttpUrl
class BookingInfo(BaseModel):
    attraction: BookingAttraction
    date: date
    time: Literal["morning", "afternoon"]
    price: Literal[2000, 2500]
class BookingData(BaseModel):
    data: BookingInfo | None


class Booking:
    def check_exist(user, connection_pool):
        con = connection_pool.get_connection()
        cursor = con.cursor(dictionary=True)
        cursor.execute(
            "select member_id, attraction_id from booking where member_id = %s",
            (user["sub"], )
        )
        data = cursor.fetchone()
        if data is None:
            return False
        else:
            return True
    def create_new(attraction, user, connection_pool):
        try:
            with connection_pool.get_connection() as con:
                cursor = con.cursor()
                cursor.execute(
                    "insert into booking(attraction_id, go_date, time, price, member_id) values(%s, %s, %s, %s, %s)",
                    (attraction.attractionId, attraction.date, attraction.time, attraction.price, user["sub"])
                )
                con.commit()
            return True
        except:
            return False
    def replace(attraction, user, connection_pool):
        try:
            with connection_pool.get_connection() as con:
                cursor = con.cursor()
                cursor.execute(
                    "update booking set attraction_id = %s, go_date = %s, time = %s, price = %s, create_date = %s where member_id = %s",
                    (attraction.attractionId, attraction.date, attraction.time, attraction.price, datetime.datetime.now(), user["sub"])
                )
                con.commit()
            return True
        except:
            return False
    def delete(user, connection_pool):
        try:
            with connection_pool.get_connection() as con:
                cursor = con.cursor(dictionary=True)
                cursor.execute(
                    "delete from booking where member_id=%s",
                    (user["sub"],)
                )
                con.commit()
            return True
        except:
            return False

class Get:
    def booking(user, connection_pool):
        with connection_pool.get_connection() as con:
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                "select attraction_id, go_date, time, price from booking where member_id = %s",
                (user["sub"],)
            )
            data = cursor.fetchone()
        return data
    def attraction(booking, connection_pool):
        with connection_pool.get_connection() as con:
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                "select id, name, address, images from attraction where id = %s",
                (booking["attraction_id"],)
            )
            data = cursor.fetchone()
            return data