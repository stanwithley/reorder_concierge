from fastapi import FastAPI

from app import routes

app = FastAPI(title="Reorder Concierge (Simple)")
app.include_router(routes.router)
