from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from lnbits.core.crud import get_user
from lnbits.core.models import WalletTypeInfo
from lnbits.decorators import (
    require_admin_key,
    require_invoice_key,
)

from .crud import (
    create_scrub_link,
    delete_scrub_link,
    get_scrub_by_wallet,
    get_scrub_link,
    get_scrub_links,
    update_scrub_link,
)
from .models import CreateScrubLink, ScrubLink

scrub_api_router = APIRouter()


@scrub_api_router.get("/api/v1/links", status_code=HTTPStatus.OK)
async def api_links(
    key_info: WalletTypeInfo = Depends(require_invoice_key),
    all_wallets: bool = Query(False),
) -> list[ScrubLink]:
    wallet_ids = [key_info.wallet.id]

    if all_wallets:
        user = await get_user(key_info.wallet.user)
        wallet_ids = user.wallet_ids if user else []

    return await get_scrub_links(wallet_ids)


@scrub_api_router.get("/api/v1/links/{link_id}", status_code=HTTPStatus.OK)
async def api_link_retrieve(
    link_id: str, key_info: WalletTypeInfo = Depends(require_invoice_key)
) -> ScrubLink:
    link = await get_scrub_link(link_id)

    if not link:
        raise HTTPException(
            detail="Scrub link does not exist.", status_code=HTTPStatus.NOT_FOUND
        )

    if link.wallet != key_info.wallet.id:
        raise HTTPException(
            detail="Not your pay link.", status_code=HTTPStatus.FORBIDDEN
        )

    return link


@scrub_api_router.post("/api/v1/links", status_code=HTTPStatus.CREATED)
@scrub_api_router.put("/api/v1/links/{link_id}", status_code=HTTPStatus.OK)
async def api_scrub_create_or_update(
    data: CreateScrubLink,
    link_id: str | None = None,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> ScrubLink:
    if link_id:
        link = await get_scrub_link(link_id)

        if not link:
            raise HTTPException(
                detail="Scrub link does not exist.", status_code=HTTPStatus.NOT_FOUND
            )

        if link.wallet != wallet.wallet.id:
            raise HTTPException(
                detail="Not your pay link.", status_code=HTTPStatus.FORBIDDEN
            )

        for k, v in data.dict().items():
            setattr(link, k, v)

        link = await update_scrub_link(link)
    else:
        wallet_has_scrub = await get_scrub_by_wallet(wallet_id=data.wallet)
        if wallet_has_scrub:
            raise HTTPException(
                detail="Wallet is already being Scrubbed",
                status_code=HTTPStatus.FORBIDDEN,
            )
        link = await create_scrub_link(data=data)

    return link


@scrub_api_router.delete("/api/v1/links/{link_id}")
async def api_link_delete(
    link_id: str, key_info: WalletTypeInfo = Depends(require_admin_key)
):
    link = await get_scrub_link(link_id)

    if not link:
        raise HTTPException(
            detail="Scrub link does not exist.", status_code=HTTPStatus.NOT_FOUND
        )

    if link.wallet != key_info.wallet.id:
        raise HTTPException(
            detail="Not your pay link.", status_code=HTTPStatus.FORBIDDEN
        )

    await delete_scrub_link(link_id)
