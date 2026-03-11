import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.database import engine
from src.models import Base
from src.utils import cleanup_expired_links
from src.routers import authorization, links

@asynccontextmanager
async def lifespan(app: FastAPI):

    task = asyncio.create_task(cleanup_expired_links())
    yield
    task.cancel()


Base.metadata.create_all(bind=engine)

app = FastAPI(lifespan=lifespan)

app.include_router(authorization.router)
app.include_router(links.router)


if __name__ == "__main__":
    uvicorn.run("src.main:app", reload=True, host="0.0.0.0", log_level="info")