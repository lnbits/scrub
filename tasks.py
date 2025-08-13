import asyncio
import json
from http import HTTPStatus
from math import floor
from urllib.parse import urlparse

import bolt11
import httpx
from fastapi import HTTPException

from lnbits.core.crud import get_standalone_payment
from lnbits.core.models import Payment
from lnbits.core.services import (
    fee_reserve_total,
    fetch_lnurl_pay_request,
    get_pr_from_lnurl,
    pay_invoice,
)
from lnbits.tasks import register_invoice_listener

from .crud import get_scrub_by_wallet


async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, "ext_scrub")

    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


async def on_invoice_paid(payment: Payment):
    if payment.extra and payment.extra.get("tag") == "scrubed":
        return

    scrub_link = await get_scrub_by_wallet(payment.wallet_id)
    if not scrub_link:
        return

    payable_amount = payment.amount - fee_reserve_total(payment.amount)

    # # DECODE LNURLP OR LNADDRESS
    try:
        payment_request = await get_pr_from_lnurl(
            scrub_link.payoraddress, payable_amount
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Failed to get payment request: {e}",
        ) from e

    rounded_amount = floor(payable_amount / 1000) * 1000
    invoice = bolt11.decode(payment_request)

    lnurlp_payment = await get_standalone_payment(invoice.payment_hash)
    # (avoid loops)
    # do not scrub yourself! :)
    if lnurlp_payment and lnurlp_payment.wallet_id == payment.wallet_id:
        return

    if invoice.amount_msat != rounded_amount:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"""
            Server returned an invalid invoice.
            Expected {payment.amount} msat, got {invoice.amount_msat}.
            """,
        )

    # PAY INVOICE
    await pay_invoice(
        wallet_id=payment.wallet_id,
        payment_request=payment_request,
        description="Scrubed",
        extra={"tag": "scrubed"},
    )
