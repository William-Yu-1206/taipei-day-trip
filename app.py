from fastapi import *
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


from router.booking import booking_router
from router.user import user_router
from router.attraction import attraction_router

app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# add router
app.include_router(user_router)
app.include_router(booking_router)
app.include_router(attraction_router)


# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/attraction.html", media_type="text/html")
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
	return FileResponse("./static/booking.html", media_type="text/html")
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
	return FileResponse("./static/thankyou.html", media_type="text/html")



