from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.db import engine
from app.models import Base

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "server is running"}


app.include_router(api_router, prefix="/api")
