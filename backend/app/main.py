from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_dashboard, routes_narrator, routes_playground, routes_review_queue
from app.db.models import Base
from app.db.session import engine
from app.proxy.router import router as proxy_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ControlPlane.ai", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proxy_router)
app.include_router(routes_dashboard.router)
app.include_router(routes_review_queue.router)
app.include_router(routes_playground.router)
app.include_router(routes_narrator.router)


@app.get("/health")
def health():
    return {"status": "ok"}
