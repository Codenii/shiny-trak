import json

from playwright.sync_api import Page, expect


def _create_hunt(page, base_url, encounter_rate=None):
    r = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": "ditto",
                "displayName": "Ditto",
                "spriteUrl": None,
                "game": None,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    hunt = r.json()
    if encounter_rate:
        page.request.put(
            f"{base_url}/api/hunts/{hunt['id']}",
            data=json.dumps({"encounterRate": encounter_rate}),
            headers={"Content-Type": "application/json"},
        )
    return hunt


def _get_overlay(page, base_url):
    return page.request.get(f"{base_url}/api/overlays").json()[0]


def test_overlay_shows_hunt_name(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlay = _get_overlay(page, base_url)

    page.goto(f"{base_url}/overlay/{overlay['name']}")
    expect(page.locator(".hunt-name", has_text="Ditto")).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_overlay_shows_count(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.request.put(
        f"{base_url}/api/hunts/{hunt['id']}",
        data=json.dumps({"count": 99}),
        headers={"Content-Type": "application/json"},
    )
    overlay = _get_overlay(page, base_url)

    page.goto(f"{base_url}/overlay/{overlay['name']}")
    expect(page.locator(".hunt-count", has_text="99")).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_overlay_count_updates_live(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlay = _get_overlay(page, base_url)

    page.goto(f"{base_url}/overlay/{overlay['name']}")
    expect(page.locator(".hunt-count", has_text="0")).to_be_visible()

    page.request.post(f"{base_url}/api/hunts/{hunt['id']}/increment")
    expect(page.locator(".hunt-card", has_text="1")).to_be_visible(timeout=5000)

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_overlay_hides_hunt_when_visibility_off(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlay = _get_overlay(page, base_url)

    update_hunts = [
        {
            "huntId": h["huntId"],
            "visible": False if h["huntId"] == hunt["id"] else h["visible"],
        }
        for h in overlay["hunts"]
    ]
    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"hunts": update_hunts}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{overlay['name']}")
    expect(page.locator(".hunt-name", has_text="Ditto")).not_to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_overlay_hides_completed_hunt(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlay = _get_overlay(page, base_url)

    page.goto(f"{base_url}/overlay/{overlay['name']}")
    expect(page.locator(".hunt-name", has_text="Ditto")).to_be_visible()

    page.request.post(
        f"{base_url}/api/hunts/{hunt['id']}/complete",
        data=json.dumps({}),
        headers={"Content-Type": "application/json"},
    )
    expect(page.locator(".hunt-name", has_text="Ditto")).not_to_be_visible(timeout=5000)

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_overlay_shows_odds_when_enabled(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url, encounter_rate=4096)
    overlay = _get_overlay(page, base_url)

    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"elements": {**overlay["elements"], "odds": True}}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{overlay['name']}")
    expect(page.locator(".hunt-odds", has_text="1/4,096")).to_be_visible()

    # Restore
    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"elements": {**overlay["elements"], "odds": False}}),
        headers={"Content-Type": "application/json"},
    )
    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_overlay_hides_name_when_disabled(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlay = _get_overlay(page, base_url)

    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"elements": {**overlay["elements"], "name": False}}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{overlay['name']}")
    expect(page.locator(".hunt-name")).not_to_be_visible()

    # Restore
    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"elements": {**overlay["elements"], "name": True}}),
        headers={"Content-Type": "application/json"},
    )
    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_overlay_hides_count_when_disabled(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlay = _get_overlay(page, base_url)

    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"elements": {**overlay["elements"], "count": False}}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{overlay['name']}")
    expect(page.locator(".hunt-count")).not_to_be_visible()

    # Restore
    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"elements": {**overlay["elements"], "count": True}}),
        headers={"Content-Type": "application/json"},
    )
    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_overlay_redirect(page: Page, base_url: str):
    page.goto(f"{base_url}/overlay")
    expect(page).to_have_url(f"{base_url}/overlay/main")


def test_overlay_not_found(page: Page, base_url: str):
    resp = page.request.get(f"{base_url}/overlay/doesnotexist")
    assert resp.status == 404
