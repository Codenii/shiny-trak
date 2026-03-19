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


def test_control_panel_loads(page: Page, base_url: str):
    page.goto(base_url)
    expect(page).to_have_title("Shiny Trak")
    expect(page.get_by_placeholder("Search Pokemon...")).to_be_visible()
    expect(page.get_by_text("Hunts", exact=True)).to_be_visible()
    expect(page.get_by_text("History", exact=True)).to_be_visible()


def test_add_hunt(page: Page, base_url: str):
    page.goto(base_url)
    page.get_by_placeholder("Search Pokemon...").fill("pikachu")
    page.get_by_role("button", name="Add Hunt").click()
    expect(page.get_by_text("Pikachu", exact=True).first).to_be_visible(timeout=15000)

    resp = page.request.get(f"{base_url}/api/hunts")
    pikachu = next((h for h in resp.json() if h["pokemon"] == "pikachu"), None)
    if pikachu:
        page.request.delete(f"{base_url}/api/hunts/{pikachu['id']}")


def test_increment_decrement(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)

    with page.expect_response(
        lambda r: "/api/hunts/" in r.url and r.request.method == "POST"
    ):
        page.locator(f"[data-hunt-id='{hunt['id']}'] button[title='Increment']").click()
    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["count"] == 1

    with page.expect_response(
        lambda r: "/api/hunts/" in r.url and r.request.method == "POST"
    ):
        page.locator(f"[data-hunt-id='{hunt['id']}'] button[title='Decrement']").click()
    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["count"] == 0

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_mark_as_found(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)
    expect(page.get_by_text("Rattata", exact=True).first).to_be_visible()

    page.locator(f"[data-hunt-id='{hunt['id']}'] button[title='Mark as Found']").click()
    expect(
        page.get_by_placeholder("How did you find it? Any thoughts...")
    ).to_be_visible()
    page.get_by_role("button", name="Mark as Found").last.click()

    page.get_by_text("History", exact=True).click()
    expect(page.get_by_text("Rattata", exact=True).first).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_overlay_renders(page: Page, base_url: str):
    overlay = page.request.post(
        f"{base_url}/api/overlays",
        data=json.dumps({"name": "test-render"}),
        headers={"Content-Type": "application/json"},
    ).json()
    page.goto(f"{base_url}/overlay/{overlay['name']}-hunt")
    expect(page.locator("#hunts")).to_be_attached()

    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")


def test_api_games(page: Page, base_url: str):
    resp = page.request.get(f"{base_url}/api/games")
    assert resp.status == 200
    games = resp.json()
    assert isinstance(games, list)
    assert len(games) > 0
    assert "Red / Blue" in games
