import datetime
import json

from playwright.sync_api import Page, expect


def _create_hunt(page: Page, base_url: str, pokemon="geodude", display="Geodude"):
    r = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": pokemon,
                "displayName": display,
                "spriteUrl": None,
                "game": None,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    return r.json()


def _open_detail(page: Page, hunt):
    page.locator(f"[data-hunt-id='{hunt['id']}']").get_by_text(
        hunt["displayName"]
    ).click()
    expect(page.locator("[data-testid='detail-count']")).to_be_visible()


def test_detail_view_opens(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)

    page.locator(f"[data-hunt-id='{hunt['id']}']").get_by_text(
        hunt["displayName"]
    ).click()

    expect(page.locator("[data-testid='detail-count']")).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_detail_view_back_button(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)
    _open_detail(page, hunt)

    page.get_by_role("button", name="Hunts").click()

    expect(page.get_by_placeholder("Search Pokemon...")).to_be_visible()
    expect(page.locator(f"[data-hunt-id='{hunt['id']}']")).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_detail_view_sidebar_nav_closes_detail(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)
    _open_detail(page, hunt)

    page.get_by_text("History", exact=True).click()

    expect(page.locator("[data-testid='detail-count']")).not_to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_detail_view_edit_count(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)
    _open_detail(page, hunt)

    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}" in r.url and r.request.method == "PUT"
    ):
        count_input = page.locator("[data-testid='detail-count']")
        count_input.fill("42")
        count_input.dispatch_event("change")

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["count"] == 42

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_detail_view_edit_start_date(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)
    _open_detail(page, hunt)

    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}" in r.url and r.request.method == "PUT"
    ):
        date_input = page.locator("[data-testid='detail-start-date']")
        date_input.fill("2026-01-15")
        date_input.dispatch_event("change")

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert datetime.date.fromtimestamp(h["startDate"]) == datetime.date(2026, 1, 15)

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_detail_view_edit_notes(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)
    _open_detail(page, hunt)

    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}" in r.url and r.request.method == "PUT"
    ):
        notes = page.locator("textarea[placeholder='Add notes about this hunt...']")
        notes.fill("Test note from E2E")
        notes.dispatch_event("blur")

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["notes"] == "Test note from E2E"

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_detail_view_completed_hunt(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.request.post(
        f"{base_url}/api/hunts/{hunt['id']}/complete",
        headers={"Content-Type": "application/json"},
    )
    page.goto(base_url)
    page.get_by_text("History", exact=True).click()

    page.locator(f"[data-hunt-id='{hunt['id']}']").get_by_text(
        hunt["displayName"]
    ).click()

    expect(page.locator("[data-testid='detail-count']")).to_be_visible()
    expect(page.locator("[data-testid='detail-end-date']")).to_be_visible()
    expect(page.get_by_text("Hotkeys", exact=True)).not_to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
