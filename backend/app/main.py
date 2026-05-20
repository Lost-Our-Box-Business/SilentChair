from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import interview, departments, activity, crm, usage, website

app = FastAPI(title="SilentChair API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview.router, prefix="/api")
app.include_router(departments.router, prefix="/api")
app.include_router(activity.router, prefix="/api")
app.include_router(crm.router, prefix="/api")
app.include_router(usage.router, prefix="/api")
app.include_router(website.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
