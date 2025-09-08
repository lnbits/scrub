import asyncio

from fastapi import APIRouter
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import scrub_generic_router
from .views_api import scrub_api_router

scheduled_tasks: list[asyncio.Task] = []
scrub_static_files = [
    {
        "path": "/scrub/static",
        "name": "scrub_static",
    }
]
scrub_ext: APIRouter = APIRouter(prefix="/scrub", tags=["scrub"])
scrub_ext.include_router(scrub_generic_router)
scrub_ext.include_router(scrub_api_router)


def scrub_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def scrub_start():
    from lnbits.tasks import create_permanent_unique_task

    task = create_permanent_unique_task("ext_scrub", wait_for_paid_invoices)
    scheduled_tasks.append(task)


__all__ = ["db", "scrub_ext", "scrub_start", "scrub_static_files", "scrub_stop"]
