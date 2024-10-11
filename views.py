from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

scrub_generic_router = APIRouter()


def scrub_renderer():
    return template_renderer(["scrub/templates"])


@scrub_generic_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return scrub_renderer().TemplateResponse(
        "scrub/index.html", {"request": request, "user": user.json()}
    )
