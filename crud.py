from typing import Optional, Union

from lnbits.db import Database
from lnbits.helpers import insert_query, update_query, urlsafe_short_hash

from .models import CreateScrubLink, ScrubLink

db = Database("ext_scrub")


async def create_scrub_link(data: CreateScrubLink) -> ScrubLink:
    scrub_id = urlsafe_short_hash()
    scrub = ScrubLink(id=scrub_id, **data.dict())
    await db.execute(
        insert_query("scrub_links", scrub),
        scrub.dict(),
    )
    return scrub


async def get_scrub_link(link_id: str) -> Optional[ScrubLink]:
    row = await db.fetchone(
        "SELECT * FROM scrub.scrub_links WHERE id = :id", {"id": link_id}
    )
    return ScrubLink(**row) if row else None


async def get_scrub_links(wallet_ids: Union[str, list[str]]) -> list[ScrubLink]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]

    q = ",".join([f"'{wallet_id}'" for wallet_id in wallet_ids])
    rows = await db.fetchall(f"SELECT * FROM scrub.scrub_links WHERE wallet IN ({q})")
    return [ScrubLink(**row) for row in rows]


async def update_scrub_link(link: ScrubLink) -> ScrubLink:
    await db.execute(
        update_query("scrub_links", link),
        link.dict(),
    )
    return link


async def delete_scrub_link(link_id: str) -> None:
    await db.execute("DELETE FROM scrub.scrub_links WHERE id = :id", {"id": link_id})


async def get_scrub_by_wallet(wallet_id) -> Optional[ScrubLink]:
    row = await db.fetchone(
        "SELECT * from scrub.scrub_links WHERE wallet = :wallet",
        {"wallet": wallet_id},
    )
    return ScrubLink(**row) if row else None


async def unique_scrubed_wallet(wallet_id):
    (row,) = await db.fetchone(
        "SELECT COUNT(wallet) FROM scrub.scrub_links WHERE wallet = :wallet",
        {"wallet": wallet_id},
    )
    return row
