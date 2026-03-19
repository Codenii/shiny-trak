import json

from playwright.sync_api import Page, expect


def _create_hunt(page, base_url):
    r = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": "zubat",
                "displayName": "Zubat",
                "spriteUrl": None,
                "game": None,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    return r.json()


def test_set_increment_hotkey(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)

    card = page.locator(f"[data-hunt-id='{hunt['id']}']")
    card.locator("button[title='Edit increment hotkey']").click()
    expect(page.get_by_text("Press a key...")).to_be_visible()

    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}" in r.url and r.request.method == "PUT"
    ):
        page.keyboard.press("Control+F9")

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["hotkey"] == "<ctrl>+<f9>"

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_set_decrement_hotkey(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)

    card = page.locator(f"[data-hunt-id='{hunt['id']}']")
    card.locator("button[title='Edit decrement hotkey']").click()
    expect(page.get_by_text("Press a key...")).to_be_visible()

    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}" in r.url and r.request.method == "PUT"
    ):
        page.keyboard.press("Shift+F9")

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["hotkeyDecrement"] == "<shift>+<f9>"

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_clear_increment_hotkey(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.request.put(
        f"{base_url}/api/hunts/{hunt['id']}",
        data=json.dumps({"hotkey": "<ctrl>+<f8>"}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(base_url)
    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}" in r.url and r.request.method == "PUT"
    ):
        page.locator(
            f"[data-hunt-id='{hunt['id']}'] button[title='Clear increment hotkey']"
        ).click()

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h.get("hotkey") is None

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_clear_decrement_hotkey(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.request.put(
        f"{base_url}/api/hunts/{hunt['id']}",
        data=json.dumps({"hotkeyDecrement": "<shift>+<f8>"}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(base_url)
    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}" in r.url and r.request.method == "PUT"
    ):
        page.locator(
            f"[data-hunt-id='{hunt['id']}'] button[title='Clear decrement hotkey']"
        ).click()

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h.get("hotkeyDecrement") is None

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_cancel_hotkey_capture(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)

    card = page.locator(f"[data-hunt-id='{hunt['id']}']")
    card.locator("button[title='Edit increment hotkey']").click()
    expect(page.get_by_text("Press a key...")).to_be_visible()

    page.locator("button[title='Cancel capture']").click()
    expect(page.get_by_text("Press a key...")).not_to_be_visible()

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h.get("hotkey") is None

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_hotkey_persistence(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.request.put(
        f"{base_url}/api/hunts/{hunt['id']}",
        data=json.dumps({"hotkey": "<ctrl>+<f7>", "hotkeyDecrement": "<shift>+<f7>"}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(base_url)
    page.reload()

    card = page.locator(f"[data-hunt-id='{hunt['id']}']")
    expect(
        card.locator("[data-testid='badge-hotkey']", has_text="Ctrl+F7")
    ).to_be_visible()
    expect(
        card.locator("[data-testid='badge-hotkey-decrement']", has_text="Shift+F7")
    ).to_be_visible()

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["hotkey"] == "<ctrl>+<f7>"
    assert h["hotkeyDecrement"] == "<shift>+<f7>"

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
