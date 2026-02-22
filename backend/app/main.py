from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from app.core.config import get_settings
from app.infrastructure.storage.mongodb import get_mongodb
from app.infrastructure.storage.redis import get_redis
from app.interfaces.dependencies import get_agent_service
from app.interfaces.api.routes import router
from app.infrastructure.logging import setup_logging
from app.interfaces.errors.exception_handlers import register_exception_handlers
from app.infrastructure.models.documents import AgentDocument, SessionDocument, UserDocument
from beanie import init_beanie

setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()

mongodb_available = False
redis_available = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongodb_available, redis_available
    logger.info("Application startup - Manus AI Agent initializing")
    
    try:
        await get_mongodb().initialize()
        await init_beanie(
            database=get_mongodb().client[settings.mongodb_database],
            document_models=[AgentDocument, SessionDocument, UserDocument]
        )
        mongodb_available = True
        logger.info("Successfully initialized MongoDB and Beanie")
    except Exception as e:
        logger.warning(f"MongoDB initialization failed (app will run with limited functionality): {e}")
        mongodb_available = False
    
    try:
        await get_redis().initialize()
        redis_available = True
        logger.info("Successfully initialized Redis")
    except Exception as e:
        logger.warning(f"Redis initialization failed (app will run with limited functionality): {e}")
        redis_available = False
    
    try:
        yield
    finally:
        logger.info("Application shutdown - Manus AI Agent terminating")
        if mongodb_available:
            try:
                await get_mongodb().shutdown()
            except Exception:
                pass
        if redis_available:
            try:
                await get_redis().shutdown()
            except Exception:
                pass

        logger.info("Cleaning up AgentService instance")
        try:
            await asyncio.wait_for(get_agent_service().shutdown(), timeout=30.0)
            logger.info("AgentService shutdown completed successfully")
        except asyncio.TimeoutError:
            logger.warning("AgentService shutdown timed out after 30 seconds")
        except Exception as e:
            logger.error(f"Error during AgentService cleanup: {str(e)}")

app = FastAPI(title="Manus AI Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(router, prefix="/api/v1")
