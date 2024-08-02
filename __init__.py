import asyncio
from loguru import logger

from fastapi import APIRouter

from lnbits.db import Database
from lnbits.helpers import template_renderer
from lnbits.tasks import create_permanent_unique_task

db = Database("ext_scrub")

scrub_static_files = [
    {
        "path": "/scrub/static",
        "name": "scrub_static",
    }
]

scrub_ext: APIRouter = APIRouter(prefix="/scrub", tags=["scrub"])


def scrub_renderer():
    return template_renderer(["scrub/templates"])


from .tasks import wait_for_paid_invoices
from .views import *  # noqa: F401,F403
from .views_api import *  # noqa: F401,F403


scheduled_tasks: list[asyncio.Task] = []


def scrub_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def scrub_start():
    task = create_permanent_unique_task("ext_scrub", wait_for_paid_invoices)
    scheduled_tasks.append(task)
