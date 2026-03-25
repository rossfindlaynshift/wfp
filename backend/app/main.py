from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import reference

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Workforce Planning", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reference.router, prefix="/api/ref", tags=["Reference Tables"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
