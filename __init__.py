import asyncio
from typing import List

from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

from lnbits.db import Database
from lnbits.helpers import template_renderer
from lnbits.tasks import catch_everything_and_restart

db = Database("ext_scrub")

scheduled_tasks: List[asyncio.Task] = []

scrub_static_files = [
    {
        "path": "/scrub/static",
        "app": StaticFiles(directory="lnbits/extensions/scrub/static"),
        "name": "scrub_static",
    }
]

scrub_ext: APIRouter = APIRouter(prefix="/scrub", tags=["scrub"])


def scrub_renderer():
    return template_renderer(["lnbits/extensions/scrub/templates"])


from .tasks import wait_for_paid_invoices
from .views import *  # noqa: F401,F403
from .views_api import *  # noqa: F401,F403


def scrub_start():
    loop = asyncio.get_event_loop()
    task = loop.create_task(catch_everything_and_restart(wait_for_paid_invoices))
    scheduled_tasks.append(task)
