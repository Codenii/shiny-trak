import json

from playwright.sync_api import Page, expect


def _create_hunt(page, base_url):
    r = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": "meowth",
                "displayName": "Meowth",
                "spriteUrl": None,
                "game": None,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    return r.json()


def test_mark_found_notes_appear_in_history(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)

    page.locator("button[title='Mark as Found']").first.click()
    expect(
        page.get_by_placeholder("How did you find it? Any thoughts...")
    ).to_be_visible()
    page.get_by_placeholder("How did you find it? Any thoughts...").fill(
        "Got it on encounter 42!"
    )

    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}/complete" in r.url
        and r.request.method == "POST"
    ):
        page.get_by_role("button", name="Mark as Found").last.click()

    page.get_by_text("History", exact=True).click()
    expect(page.get_by_text("Meowth", exact=True).first).to_be_visible()
    expect(page.get_by_text("Got it on encounter 42!")).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_mark_found_shows_count_in_history(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.request.put(
        f"{base_url}/api/hunts/{hunt['id']}",
        data=json.dumps({"count": 150}),
        headers={"Content-Type": "application/json"},
    )
    page.request.post(
        f"{base_url}/api/hunts/{hunt['id']}/complete",
        data=json.dumps({}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(base_url)
    page.get_by_text("History", exact=True).click()
    expect(
        page.locator(".bg-bg-card")
        .filter(has_text="Meowth")
        .locator(".text-gold", has_text="150")
    ).to_be_visible()

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["count"] == 150

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_mark_found_immediate_when_behavior_is_never(page: Page, base_url: str):
    page.request.put(
        f"{base_url}/api/settings",
        data=json.dumps({"mark_found_behavior": "never"}),
        headers={"Content-Type": "application/json"},
    )
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)

    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}/complete" in r.url
        and r.request.method == "POST"
    ):
        page.locator("button[title='Mark as Found']").first.click()

    expect(
        page.get_by_placeholder("How did you find it? Any thoughts...")
    ).not_to_be_visible()

    resp = page.request.get(f"{base_url}/api/hunts")
    h = next(h for h in resp.json() if h["id"] == hunt["id"])
    assert h["status"] == "completed"

    page.request.put(
        f"{base_url}/api/settings",
        data=json.dumps({"mark_found_behavior": "ask"}),
        headers={"Content-Type": "application/json"},
    )
    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_delete_from_history(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.request.post(
        f"{base_url}/api/hunts/{hunt['id']}/complete",
        data=json.dumps({}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(base_url)
    page.get_by_text("History", exact=True).click()
    expect(page.get_by_text("Meowth", exact=True).first).to_be_visible()

    with page.expect_response(
        lambda r: f"/api/hunts/{hunt['id']}" in r.url and r.request.method == "DELETE"
    ):
        page.locator(".bg-bg-card").filter(has_text="Meowth").locator(
            "button[title='Delete']"
        ).click()

    resp = page.request.get(f"{base_url}/api/hunts")
    assert not any(h["id"] == hunt["id"] for h in resp.json())


def test_completed_hunt_persists_in_history(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.request.post(
        f"{base_url}/api/hunts/{hunt['id']}/complete",
        data=json.dumps({"notes": "Persistence test"}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(base_url)
    page.reload()

    page.get_by_text("History", exact=True).click()
    expect(page.get_by_text("Meowth", exact=True).first).to_be_visible()
    expect(page.get_by_text("Persistence test")).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
