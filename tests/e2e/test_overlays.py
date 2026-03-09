import json

from playwright.sync_api import Page, expect


def _create_hunt(page, base_url):
    r = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": "magikarp",
                "displayName": "Magikarp",
                "spriteUrl": None,
                "game": None,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    return r.json()


def _create_overlay(page, base_url, name="test-overlay"):
    r = page.request.post(
        f"{base_url}/api/overlays",
        data=json.dumps({"name": name}),
        headers={"Content-Type": "application/json"},
    )
    return r.json()


def test_create_overlay(page: Page, base_url: str):
    page.goto(base_url)
    page.get_by_text("Overlays", exact=True).click()
    page.get_by_role("button", name="+ New Overlay").click()
    page.get_by_placeholder("Overlay name...").fill("overlay2")

    with page.expect_response(
        lambda r: "/api/overlays" in r.url and r.request.method == "POST"
    ):
        page.get_by_role("button", name="Add").click()

    expect(page.get_by_text("overlay2")).to_be_visible()

    resp = page.request.get(f"{base_url}/api/overlays")
    overlay = next((o for o in resp.json() if o["name"] == "overlay2"), None)
    assert overlay is not None

    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")


def test_delete_overlay(page: Page, base_url: str):
    overlay = _create_overlay(page, base_url, name="temp-overlay")

    page.goto(base_url)
    page.get_by_text("Overlays", exact=True).click()
    expect(page.get_by_text("temp-overlay")).to_be_visible()

    with page.expect_response(
        lambda r: f"/api/overlays/{overlay['id']}" in r.url
        and r.request.method == "DELETE"
    ):
        page.locator(".bg-bg-card").filter(has_text="temp-overlay").locator(
            "button[title='Delete overlay']"
        ).click()

    resp = page.request.get(f"{base_url}/api/overlays")
    assert not any(o["id"] == overlay["id"] for o in resp.json())


def test_delete_overlay_disabled_when_only_one(page: Page, base_url: str):
    # Ensure only the default overlay exists
    overlays = page.request.get(f"{base_url}/api/overlays").json()
    assert len(overlays) == 1

    page.goto(base_url)
    page.get_by_text("Overlays", exact=True).click()
    expect(page.locator("button[title='Delete overlay']")).to_be_disabled()


def test_toggle_hunt_visibility(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlays = page.request.get(f"{base_url}/api/overlays").json()
    overlay = overlays[0]

    page.goto(base_url)
    page.get_by_text("Overlays", exact=True).click()
    page.get_by_text(overlay["name"]).first.click()

    with page.expect_response(
        lambda r: f"/api/overlays/{overlay['id']}" in r.url
        and r.request.method == "PUT"
    ):
        page.locator("label").filter(has_text="Magikarp").locator(
            "input[type='checkbox']"
        ).click()

    resp = page.request.get(f"{base_url}/api/overlays")
    updated = next(o for o in resp.json() if o["id"] == overlay["id"])
    entry = next((h for h in updated["hunts"] if h["huntId"] == hunt["id"]), None)
    assert entry is not None and entry["visible"] is False

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_overlay_element_toggle_odds(page: Page, base_url: str):
    overlays = page.request.get(f"{base_url}/api/overlays").json()
    overlay = overlays[0]

    page.goto(base_url)
    page.get_by_text("Overlays", exact=True).click()
    page.get_by_text(overlay["name"]).first.click()

    with page.expect_response(
        lambda r: f"/api/overlays/{overlay['id']}" in r.url
        and r.request.method == "PUT"
    ):
        page.locator("label").filter(has_text="Odds").locator(
            "input[type='checkbox']"
        ).click()

    resp = page.request.get(f"{base_url}/api/overlays")
    updated = next(o for o in resp.json() if o["id"] == overlay["id"])
    assert updated["elements"]["odds"] is True

    # Restore
    with page.expect_response(
        lambda r: f"/api/overlays/{overlay['id']}" in r.url
        and r.request.method == "PUT"
    ):
        page.locator("label").filter(has_text="Odds").locator(
            "input[type='checkbox']"
        ).click()

    resp = page.request.get(f"{base_url}/api/overlays")
    updated = next(o for o in resp.json() if o["id"] == overlay["id"])
    assert updated["elements"]["odds"] is False


def test_overlay_element_toggle_sprite(page: Page, base_url: str):
    overlays = page.request.get(f"{base_url}/api/overlays").json()
    overlay = overlays[0]

    page.goto(base_url)
    page.get_by_text("Overlays", exact=True).click()
    page.get_by_text(overlay["name"]).first.click()

    with page.expect_response(
        lambda r: f"/api/overlays/{overlay['id']}" in r.url
        and r.request.method == "PUT"
    ):
        page.locator("label").filter(has_text="Sprite").locator(
            "input[type='checkbox']"
        ).click()

    resp = page.request.get(f"{base_url}/api/overlays")
    updated = next(o for o in resp.json() if o["id"] == overlay["id"])
    assert updated["elements"]["sprite"] is False

    # Restore
    with page.expect_response(
        lambda r: f"/api/overlays/{overlay['id']}" in r.url
        and r.request.method == "PUT"
    ):
        page.locator("label").filter(has_text="Sprite").locator(
            "input[type='checkbox']"
        ).click()

    resp = page.request.get(f"{base_url}/api/overlays")
    updated = next(o for o in resp.json() if o["id"] == overlay["id"])
    assert updated["elements"]["sprite"] is True


def test_overlay_persistence(page: Page, base_url: str):
    overlay = _create_overlay(page, base_url, name="persist-overlay")

    page.goto(base_url)
    page.reload()
    page.get_by_text("Overlays", exact=True).click()
    expect(page.get_by_text("persist-overlay")).to_be_visible()

    resp = page.request.get(f"{base_url}/api/overlays")
    assert any(o["name"] == "persist-overlay" for o in resp.json())

    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")


def test_copy_overlay_url(page: Page, context, base_url: str):
    context.grant_permissions(["clipboard-read", "clipboard-write"])
    overlays = page.request.get(f"{base_url}/api/overlays").json()
    overlay = overlays[0]

    page.goto(base_url)
    page.get_by_text("Overlays", exact=True).click()
    page.locator("button[title='Copy overlay URL']").first.click()

    clipboard_text = page.evaluate("async () => await navigator.clipboard.readText()")
    assert f"/overlay/{overlay['name']}" in clipboard_text
