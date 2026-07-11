from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import interview, departments, activity, crm, usage, website, living_doc, tasks, agents, website_public

app = FastAPI(title="SilentChair API", version="0.1.0")

_allowed_origins = list({
    settings.frontend_url,
    "http://localhost:3000",
    "https://silentchair.app",
    "https://www.silentchair.app",
})

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"https://.*\.silentchair\.app",
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
app.include_router(living_doc.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(website_public.router, prefix="/public")


@app.get("/health")
def health():
    return {"status": "ok"}
