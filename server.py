from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# статика
app.mount("/static", StaticFiles(directory="webapp"), name="static")

@app.get("/")
def index():
    return FileResponse("webapp/index.html")
