import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.seed import seed_runtime_state
from app.services.bot_runtime import bot_background_loop
from app.services.deploy_ops import DeploymentOpsService
from app.services.operations import OperationsService

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_runtime_state()
    with SessionLocal() as db:
        OperationsService(db).mark_startup()
    stop_event = asyncio.Event()
    loop_task = asyncio.create_task(bot_background_loop(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        loop_task.cancel()
        try:
            await loop_task
        except BaseException:
            pass
        with SessionLocal() as db:
            OperationsService(db).mark_shutdown()


app = FastAPI(
    title=settings.project_name,
    version='0.9.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/healthz', tags=['health'])
async def healthz() -> dict[str, object]:
    with SessionLocal() as db:
        state = OperationsService(db).system_health()
        readiness = DeploymentOpsService(db).release_readiness()
    return {'status': 'ok', 'service': settings.project_name, 'state': state, 'readiness': readiness}


app.include_router(api_router, prefix=settings.api_v1_prefix)
