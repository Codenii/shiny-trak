import json

from playwright.sync_api import Page, expect


def _create_hunt(page, base_url):
    r = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": "rattata",
                "displayName": "Rattata",
                "spriteUrl": None,
                "game": None,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    return r.json()


def test_reset_count(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.request.post(f"{base_url}/api/hunts/{hunt['id']}/increment")
    page.request.post(f"{base_url}/api/hunts/{hunt['id']}/increment")
    page.request.post(f"{base_url}/api/hunts/{hunt['id']}/increment")

    page.goto(base_url)
    page.locator("button[title='Reset count']").first.click()

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["count"] == 0

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_manual_count_entry(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)

    page.goto(base_url)
    count_input = page.locator("input.text-gold").first
    count_input.fill("42")
    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}" in r.url and r.request.method == "PUT"
    ):
        count_input.dispatch_event("change")

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["count"] == 42

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_count_cannot_go_below_zero(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)

    page.goto(base_url)
    page.get_by_role("button", name="-", exact=True).first.click()

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["count"] == 0

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_count_persistence(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)

    page.request.put(
        f"{base_url}/api/hunts/{hunt['id']}",
        data=json.dumps({"count": 77}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(base_url)
    page.reload()
    expect(page.locator("input.text-gold").first).to_have_value("77")

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["count"] == 77

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
