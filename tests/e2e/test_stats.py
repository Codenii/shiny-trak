import json

from playwright.sync_api import Page, expect


def test_stats_endpoint(page: Page, base_url: str):
    r1 = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": "bulbasaur",
                "displayName": "Bulbasaur",
                "spriteUrl": None,
                "game": "Red / Blue",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": "squirtle",
                "displayName": "Squirtle",
                "spriteUrl": None,
                "game": None,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    h1 = r1.json()

    # Mark 1 as completed
    page.request.post(
        f"{base_url}/api/hunts/{h1['id']}/complete",
        data=json.dumps({}),
        headers={"Content-Type": "application/json"},
    )

    # Check Stats
    r = page.request.get(f"{base_url}/api/stats")
    data = r.json()
    assert data["totalCompleted"] == 1
    assert data["totalActive"] == 1
    assert data["byGame"]["Red / Blue"]["completed"] == 1
    assert data["byGame"]["None"]["active"] == 1

    hunts = page.request.get(f"{base_url}/api/hunts?scope=all").json()
    for h in hunts:
        if h["pokemon"] in ("bulbasaur", "squirtle"):
            page.request.delete(f"{base_url}/api/hunts/{h['id']}")


def test_stats_ui(page: Page, base_url: str):
    # Complete hunt with game
    r1 = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": "bulbasaur",
                "displayName": "Bulbasaur",
                "spriteUrl": None,
                "game": "Red / Blue",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    h1 = r1.json()
    page.request.post(
        f"{base_url}/api/hunts/{h1['id']}/complete",
        data=json.dumps({}),
        headers={"Content-Type": "application/json"},
    )

    # Active hunt with game
    page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": "charmander",
                "displayName": "Charmander",
                "spriteUrl": None,
                "game": "Red / Blue",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    # Complete hunt with no game
    r3 = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": "squirtle",
                "displayName": "Squirtle",
                "spriteUrl": None,
                "game": None,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    h3 = r3.json()
    page.request.post(
        f"{base_url}/api/hunts/{h3['id']}/complete",
        data=json.dumps({}),
        headers={"Content-Type": "application/json"},
    )

    # Active hunt with no game
    page.request.post(
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

    # Nav to stats tab
    page.goto(base_url)
    page.get_by_text("Statistics", exact=True).click()

    # Overall counts
    expect(page.locator("#stats-overall .text-3xl.text-gold").first).to_have_text("2")
    expect(
        page.locator("#stats-overall .text-3xl.text-primary-light").first
    ).to_have_text("2")

    # By Game - Red / Blue
    red_blue_row = page.locator("#stats-by-game [data-game='Red / Blue']")
    expect(red_blue_row.locator(".text-gold.font-semibold")).to_have_text("1")
    expect(red_blue_row.locator(".text-primary-light.font-semibold")).to_have_text("1")

    # By Game - No Game
    no_game_row = page.locator("#stats-by-game [data-game='No Game']")
    expect(no_game_row.locator(".text-gold.font-semibold")).to_have_text("1")
    expect(no_game_row.locator(".text-primary-light.font-semibold")).to_have_text("1")

    # Cleanup
    hunts = page.request.get(f"{base_url}/api/hunts?scope=all").json()
    for h in hunts:
        if h["pokemon"] in ("bulbasaur", "charmander", "squirtle", "rattata"):
            page.request.delete(f"{base_url}/api/hunts/{h['id']}")
