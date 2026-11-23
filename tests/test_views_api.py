from contextlib import nullcontext
from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from lnbits import decorators
from lnbits.core.db import db
from lnbits.core.models import Wallet

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
    other_wallet = Wallet(
        id="wallet-two",
        user="user-two",
        name="Other wallet",
        adminkey="other-admin-key",
        inkey="other-invoice-key",
    )
    wallets = (wallet, other_wallet)
    wallets_by_key = {key: w for w in wallets for key in (w.adminkey, w.inkey)}
    monkeypatch.setattr(db, "connect", nullcontext)
    monkeypatch.setattr(
        decorators,
        "get_wallet_for_key",
        AsyncMock(side_effect=lambda key, **_: wallets_by_key.get(key)),
    )
    monkeypatch.setattr(decorators, "_check_user_access", AsyncMock())

    link = ScrubLink(
        id="link-one",
        wallet=wallet.id,
        description="Original",
        payoraddress="original@example.com",
    )
    other_link = ScrubLink(
        id="link-two",
        wallet=other_wallet.id,
        description="Other original",
        payoraddress="other@example.com",
    )
    links = {link.id: link, other_link.id: other_link}
    lookup = AsyncMock(return_value=None)
    create = AsyncMock(return_value=link)
    update = AsyncMock(side_effect=lambda value: value)
    delete = AsyncMock(side_effect=links.pop)
    monkeypatch.setattr(views_api, "get_scrub_link", AsyncMock(side_effect=links.get))
    monkeypatch.setattr(
        views_api,
        "get_scrub_links",
        AsyncMock(
            side_effect=lambda ids: [
                item for item in links.values() if item.wallet in ids
            ]
        ),
    )
    monkeypatch.setattr(
        views_api,
        "get_user",
        AsyncMock(
            side_effect=lambda user_id: SimpleNamespace(
                wallet_ids=[w.id for w in wallets if w.user == user_id]
            )
        ),
    )
    monkeypatch.setattr(views_api, "get_scrub_by_wallet", lookup)
    monkeypatch.setattr(views_api, "create_scrub_link", create)
    monkeypatch.setattr(views_api, "update_scrub_link", update)
    monkeypatch.setattr(views_api, "delete_scrub_link", delete)
    app = FastAPI()
    app.include_router(views_api.scrub_api_router, prefix="/scrub")
    with TestClient(app, headers={"X-API-KEY": wallet.adminkey}) as client:
        yield SimpleNamespace(
            client=client,
            wallet=wallet,
            other_wallet=other_wallet,
            link=link,
            other_link=other_link,
            lookup=lookup,
            create=create,
            update=update,
            delete=delete,
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
            "wallet": api.other_wallet.id,
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
    response = api.client.post(
        "/scrub/api/v1/links", json={**payload, "id": api.other_link.id}
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == api.link.model_dump()
    api.lookup.assert_awaited_once_with(wallet_id=api.wallet.id)
    api.create.assert_awaited_once()
    assert api.create.call_args.kwargs["data"].model_dump() == payload


@pytest.mark.parametrize("with_link_id", [False, True])
def test_create_link_for_wallet_with_existing_link(api, with_link_id):
    api.lookup.return_value = api.link
    response = api.client.post(
        "/scrub/api/v1/links",
        params={"link_id": api.link.id} if with_link_id else {},
        json=api.link.model_dump(exclude={"id"}),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"] == "Wallet is already being Scrubbed"
    api.create.assert_not_awaited()
    api.update.assert_not_awaited()


def test_update_link_for_request_wallet(api):
    link_id = api.link.id
    response = api.client.put(
        f"/scrub/api/v1/links/{link_id}",
        json={
            "id": api.other_link.id,
            "wallet": api.wallet.id,
            "description": "Updated",
            "payoraddress": "updated@example.com",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()["id"] == link_id
    assert response.json()["wallet"] == api.wallet.id
    assert response.json()["description"] == "Updated"
    assert response.json()["payoraddress"] == "updated@example.com"
    api.update.assert_awaited_once_with(api.link)
    api.create.assert_not_awaited()


def test_update_link_from_another_wallet(api):
    original = api.other_link.model_dump()
    response = api.client.put(
        f"/scrub/api/v1/links/{api.other_link.id}",
        json={
            "wallet": api.wallet.id,
            "description": "Updated",
            "payoraddress": "updated@example.com",
        },
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"] == "Not your pay link."
    assert api.other_link.model_dump() == original
    api.update.assert_not_awaited()


@pytest.mark.parametrize("method", ["GET", "DELETE"])
def test_link_path_is_scoped_to_key_wallet(api, method):
    path = f"/scrub/api/v1/links/{api.other_link.id}"
    response = api.client.request(method, path)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"] == "Not your pay link."
    api.delete.assert_not_awaited()

    owner_response = api.client.request(
        method, path, headers={"X-API-KEY": api.other_wallet.adminkey}
    )
    assert owner_response.status_code == HTTPStatus.OK
    if method == "GET":
        assert owner_response.json() == api.other_link.model_dump()
    else:
        api.delete.assert_awaited_once_with(api.other_link.id)


@pytest.mark.parametrize("all_wallets", [False, True])
def test_link_list_does_not_include_other_users_wallets(api, all_wallets):
    response = api.client.get(
        "/scrub/api/v1/links", params={"all_wallets": all_wallets}
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == [api.link.model_dump()]


def test_update_missing_link(api):
    response = api.client.put(
        "/scrub/api/v1/links/missing",
        json=api.link.model_dump(exclude={"id"}),
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    api.update.assert_not_awaited()
