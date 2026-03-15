import json

from playwright.sync_api import Page, expect


def test_milestone_banner_appears_in_control_panel(page: Page, base_url: str):
    r = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": "pikachu",
                "displayName": "Pikachu",
                "spriteUrl": None,
                "game": None,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    hunt = r.json()
    page.request.put(
        f"{base_url}/api/hunts/{hunt['id']}",
        data=json.dumps({"encounterRate": 3, "count": 2}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(base_url)
    page.wait_for_selector(".bg-bg-card")

    page.request.post(f"{base_url}/api/hunts/{hunt['id']}/increment")
    expect(page.get_by_text("Pikachu reached 1x odds!")).to_be_visible(timeout=5000)

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_milestone_banner_hidden_when_disabled(page: Page, base_url: str):
    page.request.put(
        f"{base_url}/api/settings",
        data=json.dumps({"milestone_alerts": False}),
        headers={"Content-Type": "application/json"},
    )

    r = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": "pikachu",
                "displayName": "Pikachu",
                "spriteUrl": None,
                "game": None,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    hunt = r.json()
    page.request.put(
        f"{base_url}/api/hunts/{hunt['id']}",
        data=json.dumps({"encounterRate": 3, "count": 2}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(base_url)
    page.wait_for_selector(".bg-bg-card")

    page.request.post(f"{base_url}/api/hunts/{hunt['id']}/increment")
    expect(page.get_by_text("Pikachu reached 1x odds!")).to_be_hidden(timeout=2000)

    page.request.put(
        f"{base_url}/api/settings",
        data=json.dumps({"milestone_alerts": True}),
        headers={"Content-Type": "application/json"},
    )
    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
