from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from lnbits.core.models import KeyType, Wallet, WalletTypeInfo
from lnbits.decorators import require_admin_key

from .. import views_api
from ..models import ScrubLink


@pytest.fixture
def api(monkeypatch):
    wallet = Wallet(
        id="wallet-one",
        user="user-one",
        name="Wallet",
        adminkey="admin-key",
        inkey="invoice-key",
    )
    key_info = WalletTypeInfo(key_type=KeyType.admin, wallet=wallet)
    link = ScrubLink(
        id="link-one",
        wallet=wallet.id,
        description="Original",
        payoraddress="original@example.com",
    )
    lookup = AsyncMock(return_value=None)
    retrieve = AsyncMock(return_value=link)
    create = AsyncMock(return_value=link)
    update = AsyncMock(side_effect=lambda value: value)
    monkeypatch.setattr(views_api, "get_scrub_by_wallet", lookup)
    monkeypatch.setattr(views_api, "get_scrub_link", retrieve)
    monkeypatch.setattr(views_api, "create_scrub_link", create)
    monkeypatch.setattr(views_api, "update_scrub_link", update)
    app = FastAPI()
    app.include_router(views_api.scrub_api_router, prefix="/scrub")
    app.dependency_overrides[require_admin_key] = lambda: key_info
    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client,
            wallet=wallet,
            link=link,
            lookup=lookup,
            retrieve=retrieve,
            create=create,
            update=update,
        )


@pytest.mark.parametrize("method", ["POST", "PUT"])
def test_link_wallet_must_match_request_wallet(api, method):
    path = "/scrub/api/v1/links"
    if method == "PUT":
        path += f"/{api.link.id}"
    response = api.client.request(
        method,
        path,
        json={
            "wallet": "wallet-two",
            "description": "Updated",
            "payoraddress": "updated@example.com",
        },
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"] == "Not your pay link."
    api.lookup.assert_not_awaited()
    api.create.assert_not_awaited()
    api.update.assert_not_awaited()
    assert api.link.wallet == api.wallet.id
    assert api.link.description == "Original"


def test_create_link_for_request_wallet(api):
    payload = api.link.model_dump(exclude={"id"})
    response = api.client.post("/scrub/api/v1/links", json=payload)

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == api.link.model_dump()
    api.lookup.assert_awaited_once_with(wallet_id=api.wallet.id)
    api.create.assert_awaited_once()
    assert api.create.call_args.kwargs["data"].model_dump() == payload


def test_create_link_for_wallet_with_existing_link(api):
    api.lookup.return_value = api.link
    response = api.client.post(
        "/scrub/api/v1/links", json=api.link.model_dump(exclude={"id"})
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"] == "Wallet is already being Scrubbed"
    api.create.assert_not_awaited()


def test_update_link_for_request_wallet(api):
    response = api.client.put(
        f"/scrub/api/v1/links/{api.link.id}",
        json={
            "wallet": api.wallet.id,
            "description": "Updated",
            "payoraddress": "updated@example.com",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()["wallet"] == api.wallet.id
    assert response.json()["description"] == "Updated"
    assert response.json()["payoraddress"] == "updated@example.com"
    api.update.assert_awaited_once_with(api.link)
    api.create.assert_not_awaited()


def test_update_link_from_another_wallet(api):
    api.link.wallet = "wallet-two"
    response = api.client.put(
        f"/scrub/api/v1/links/{api.link.id}",
        json={
            "wallet": api.wallet.id,
            "description": "Updated",
            "payoraddress": "updated@example.com",
        },
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"] == "Not your pay link."
    assert api.link.wallet == "wallet-two"
    assert api.link.description == "Original"
    api.update.assert_not_awaited()


def test_update_missing_link(api):
    api.retrieve.return_value = None
    response = api.client.put(
        "/scrub/api/v1/links/missing",
        json=api.link.model_dump(exclude={"id"}),
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    api.update.assert_not_awaited()
