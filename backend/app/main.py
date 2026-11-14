from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.redis import create_redis_client
from sqlalchemy import text
from app.routes.students_routes import router as student_router
from app.routes.file_route import router as file_router
from app.core.database import engine





@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    app.state.redis = await create_redis_client()

    try:
        yield
    finally:
        await app.state.redis.aclose()
        await engine.dispose()

   

app = FastAPI(title="Space File" , lifespan=lifespan)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         
    allow_credentials=False,     
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(student_router, prefix="/students", tags=["Students"])
app.include_router(file_router, prefix="/files", tags=["Files"])


@app.get("/home")
def home():
    return {"Message": "Checking Server"}

@app.get("/test-redis")
async def test_redis():
    redis = app.state.redis

    await redis.set("project_status", "Redis Connected")

    value = await redis.get("project_status")

    return {"redis": value}