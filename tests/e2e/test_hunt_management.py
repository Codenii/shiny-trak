import json

from playwright.sync_api import Page, expect


def _create_hunt(page, base_url, pokemon="geodude", display="Geodude"):
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


def test_delete_hunt(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)
    expect(page.get_by_text("Geodude", exact=True).first).to_be_visible()

    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}" in r.url and r.request.method == "DELETE"
    ):
        page.locator(
            f"[data-hunt-id='{hunt['id']}'] button[title='Delete Hunt']"
        ).click()

    resp = page.request.get(f"{base_url}/api/hunts")
    assert not any(h["id"] == hunt["id"] for h in resp.json())


def test_set_encounter_rate(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)

    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}" in r.url and r.request.method == "PUT"
    ):
        odds_input = page.locator(
            f"[data-hunt-id='{hunt['id']}'] input[placeholder='Odds']"
        )
        odds_input.fill("4096")
        odds_input.dispatch_event("change")

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["encounterRate"] == 4096

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_change_game(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)

    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}" in r.url and r.request.method == "PUT"
    ):
        page.locator(f"[data-hunt-id='{hunt['id']}'] select").select_option(
            label="Scarlet / Violet"
        )

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["game"] == "Scarlet / Violet"

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_add_hunt_with_game(page: Page, base_url: str):
    page.goto(base_url)
    page.get_by_placeholder("Search Pokemon...").fill("snorlax")
    page.locator("select").first.select_option(label="Scarlet / Violet")
    page.get_by_role("button", name="Add Hunt").click()
    expect(page.get_by_text("Snorlax", exact=True).first).to_be_visible(timeout=15000)

    resp = page.request.get(f"{base_url}/api/hunts")
    snorlax = next((h for h in resp.json() if h["pokemon"] == "snorlax"), None)
    assert snorlax is not None
    assert snorlax["game"] == "Scarlet / Violet"

    page.request.delete(f"{base_url}/api/hunts/{snorlax['id']}")
