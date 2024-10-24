from typing import Optional, Union

from lnbits.db import Database
from lnbits.helpers import urlsafe_short_hash

from .models import CreateScrubLink, ScrubLink

db = Database("ext_scrub")


async def create_scrub_link(data: CreateScrubLink) -> ScrubLink:
    scrub_id = urlsafe_short_hash()
    scrub = ScrubLink(id=scrub_id, **data.dict())
    await db.insert("scrub.scrub_links", scrub)
    return scrub


async def get_scrub_link(link_id: str) -> Optional[ScrubLink]:
    return await db.fetchone(
        "SELECT * FROM scrub.scrub_links WHERE id = :id",
        {"id": link_id},
        ScrubLink,
    )


async def get_scrub_links(wallet_ids: Union[str, list[str]]) -> list[ScrubLink]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]

    q = ",".join([f"'{wallet_id}'" for wallet_id in wallet_ids])
    return await db.fetchall(
        f"SELECT * FROM scrub.scrub_links WHERE wallet IN ({q})", model=ScrubLink
    )


async def update_scrub_link(link: ScrubLink) -> ScrubLink:
    await db.update("scrub.scrub_links", link)
    return link


async def delete_scrub_link(link_id: str) -> None:
    await db.execute("DELETE FROM scrub.scrub_links WHERE id = :id", {"id": link_id})


async def get_scrub_by_wallet(wallet_id) -> Optional[ScrubLink]:
    return await db.fetchone(
        "SELECT * from scrub.scrub_links WHERE wallet = :wallet",
        {"wallet": wallet_id},
        ScrubLink,
    )


async def unique_scrubed_wallet(wallet_id):
    result = await db.execute(
        "SELECT COUNT(wallet) FROM scrub.scrub_links WHERE wallet = :wallet",
        {"wallet": wallet_id},
    )
    count = result.fetchone()[0]
    return count
