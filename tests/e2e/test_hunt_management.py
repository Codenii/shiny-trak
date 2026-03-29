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


def _create_overlay(page, base_url, name, type_="hunt"):
    r = page.request.post(
        f"{base_url}/api/overlays",
        data=json.dumps({"name": name, "type": type_}),
        headers={"Content-Type": "application/json"},
    )
    return r.json()


def test_delete_hunt(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)
    expect(page.locator(f"[data-hunt-id='{hunt['id']}']")).to_be_visible()

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
    page.locator("[data-testid='add-hunt-game-select']").select_option(
        label="Scarlet / Violet"
    )

    with page.expect_response(
        lambda r: "/api/hunts" in r.url and r.request.method == "POST"
    ) as response_info:
        page.get_by_role("button", name="Add Hunt").click()

    snorlax = response_info.value.json()
    expect(page.locator(f"[data-hunt-id='{snorlax['id']}']")).to_be_visible(
        timeout=15000
    )

    assert snorlax["game"] == "Scarlet / Violet"

    page.request.delete(f"{base_url}/api/hunts/{snorlax['id']}")


def test_add_hunt_assigns_to_selected_overlay(page: Page, base_url: str):
    overlay = _create_overlay(page, base_url, name="picker_test")
    page.goto(base_url)

    page.get_by_placeholder("Search Pokemon...").fill("rattata")
    page.locator("[data-testid='overlay-picker-trigger']").click()
    page.locator(
        f"[data-testid='overlay-picker-popover'] [data-overlay-id='{overlay['id']}'] input[type='checkbox']"
    ).check()

    with page.expect_response(
        lambda r: "/api/hunts" in r.url and r.request.method == "POST"
    ) as response_info:
        page.get_by_role("button", name="Add Hunt").click()

    hunt = response_info.value.json()
    expect(page.locator(f"[data-hunt-id='{hunt['id']}']")).to_be_visible(timeout=15000)

    all_overlays = page.request.get(f"{base_url}/api/overlays").json()
    updated = next(o for o in all_overlays if o["id"] == overlay["id"])
    assert any(h["huntId"] == hunt["id"] for h in updated["hunts"])

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")


def test_add_hunt_select_all_overlays(page: Page, base_url: str):
    overlay1 = _create_overlay(page, base_url, name="select-all-1")
    overlay2 = _create_overlay(page, base_url, name="select-all-2")
    page.goto(base_url)

    page.get_by_placeholder("Search Pokemon...").fill("sentret")
    page.locator("[data-testid='overlay-picker-trigger']").click()
    page.locator("[data-testid='select-all-overlays']").check()

    with page.expect_response(
        lambda r: "/api/hunts" in r.url and r.request.method == "POST"
    ) as response_info:
        page.get_by_role("button", name="Add Hunt").click()

    hunt = response_info.value.json()
    expect(page.locator(f"[data-hunt-id='{hunt['id']}']")).to_be_visible(timeout=15000)

    all_overlays = page.request.get(f"{base_url}/api/overlays").json()
    for overlay in [overlay1, overlay2]:
        updated = next(o for o in all_overlays if o["id"] == overlay["id"])
        assert any(h["huntId"] == hunt["id"] for h in updated["hunts"])

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
    page.request.delete(f"{base_url}/api/overlays/{overlay1['id']}")
    page.request.delete(f"{base_url}/api/overlays/{overlay2['id']}")


def test_add_hunt_creates_overlay_from_form(page: Page, base_url: str):
    page.goto(base_url)

    page.get_by_placeholder("Search Pokemon...").fill("hoothoot")
    page.locator("[data-testid='overlay-picker-trigger']").click()
    page.locator("[data-testid='show-new-overlay-form']").click()

    with page.expect_response(
        lambda r: "/api/overlays" in r.url and r.request.method == "POST"
    ):
        page.locator("[data-testid='new-overlay-name-input']").fill("from-form-overlay")
        page.locator("[data-testid='add-overlay-from-form']").click()

    with page.expect_response(
        lambda r: "api/hunts" in r.url and r.request.method == "POST"
    ) as response_info:
        page.get_by_role("button", name="Add Hunt").click()

    hunt = response_info.value.json()
    expect(page.locator(f"[data-hunt-id='{hunt['id']}']")).to_be_visible(timeout=15000)

    overlays_resp = page.request.get(f"{base_url}/api/overlays")
    overlay = next(
        (o for o in overlays_resp.json() if o["name"] == "from-form-overlay"), None
    )
    assert overlay is not None
    assert any(h["huntId"] == hunt["id"] for h in overlay["hunts"])

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")
