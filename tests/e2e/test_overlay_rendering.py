import json

from playwright.sync_api import Page, expect


def _create_hunt(page, base_url, encounter_rate=None, game=None, name="ditto"):
    r = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": name,
                "displayName": name.title(),
                "spriteUrl": None,
                "game": game,
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


def _create_overlay(page: Page, base_url: str):
    r = page.request.post(
        f"{base_url}/api/overlays",
        data=json.dumps({"name": "test-hunt-ov"}),
        headers={"Content-Type": "application/json"},
    )
    return r.json()


def _create_stats_overlay(page: Page, base_url: str, name: str):
    r = page.request.post(
        f"{base_url}/api/overlays",
        data=json.dumps({"name": name, "type": "stats"}),
        headers={"Content-Type": "application/json"},
    )
    return r.json()


def test_overlay_shows_hunt_name(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlay = _create_overlay(page, base_url)

    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"hunts": [{"huntId": hunt["id"], "visible": True}]}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{overlay['name']}-hunt")
    expect(page.locator(".hunt-name", has_text="Ditto")).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")


def test_overlay_shows_count(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.request.put(
        f"{base_url}/api/hunts/{hunt['id']}",
        data=json.dumps({"count": 99}),
        headers={"Content-Type": "application/json"},
    )
    overlay = _create_overlay(page, base_url)

    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"hunts": [{"huntId": hunt["id"], "visible": True}]}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{overlay['name']}-hunt")
    expect(page.locator(".hunt-count", has_text="99")).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")


def test_overlay_count_updates_live(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlay = _create_overlay(page, base_url)

    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"hunts": [{"huntId": hunt["id"], "visible": True}]}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{overlay['name']}-hunt")
    expect(page.locator(".hunt-count", has_text="0")).to_be_visible()

    page.request.post(f"{base_url}/api/hunts/{hunt['id']}/increment")
    expect(page.locator(".hunt-count", has_text="1")).to_be_visible(timeout=5000)

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")


def test_overlay_hides_hunt_when_visibility_off(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlay = _create_overlay(page, base_url)

    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"hunts": [{"huntId": hunt["id"], "visible": False}]}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{overlay['name']}-hunt")
    expect(page.locator(".hunt-name", has_text="Ditto")).not_to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")


def test_overlay_hides_completed_hunt(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlay = _create_overlay(page, base_url)

    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"hunts": [{"huntId": hunt["id"], "visible": True}]}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{overlay['name']}-hunt")
    expect(page.locator(".hunt-name", has_text="Ditto")).to_be_visible()

    page.request.post(
        f"{base_url}/api/hunts/{hunt['id']}/complete",
        data=json.dumps({}),
        headers={"Content-Type": "application/json"},
    )
    expect(page.locator(".hunt-name", has_text="Ditto")).not_to_be_visible(timeout=5000)

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")


def test_overlay_shows_odds_when_enabled(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url, encounter_rate=4096)
    overlay = _create_overlay(page, base_url)

    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"hunts": [{"huntId": hunt["id"], "visible": True}]}),
        headers={"Content-Type": "application/json"},
    )
    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"elements": {**overlay["elements"], "odds": True}}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{overlay['name']}-hunt")
    expect(page.locator(".hunt-odds", has_text="1/4,096")).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")


def test_overlay_hides_name_when_disabled(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlay = _create_overlay(page, base_url)

    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"hunts": [{"huntId": hunt["id"], "visible": True}]}),
        headers={"Content-Type": "application/json"},
    )
    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"elements": {**overlay["elements"], "name": False}}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{overlay['name']}-hunt")
    expect(page.locator(".hunt-name")).not_to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")


def test_overlay_hides_count_when_disabled(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    overlay = _create_overlay(page, base_url)

    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"hunts": [{"huntId": hunt["id"], "visible": True}]}),
        headers={"Content-Type": "application/json"},
    )
    page.request.put(
        f"{base_url}/api/overlays/{overlay['id']}",
        data=json.dumps({"elements": {**overlay["elements"], "count": False}}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{overlay['name']}-hunt")
    expect(page.locator(".hunt-count")).not_to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
    page.request.delete(f"{base_url}/api/overlays/{overlay['id']}")


def test_overlay_not_found(page: Page, base_url: str):
    resp = page.request.get(f"{base_url}/overlay/doesntexist")
    assert resp.status == 404


def test_overlay_bare_path_not_found(page: Page, base_url: str):
    resp = page.request.get(f"{base_url}/overlay")
    assert resp.status == 404


def test_stats_overlay_shows_total_completed(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)

    page.request.post(
        f"{base_url}/api/hunts/{hunt['id']}/complete",
        data=json.dumps({}),
        headers={"Content-Type": "application/json"},
    )
    stats_ov = _create_stats_overlay(page, base_url, name="test-stats-total")

    page.goto(f"{base_url}/overlay/{stats_ov['name']}-stats")
    expect(
        page.locator(".stat-line", has_text="Total Completed: 1 hunt")
    ).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")
    page.request.delete(f"{base_url}/api/overlays/{stats_ov['id']}")


def test_stats_overlay_breakdown_completed(page: Page, base_url: str):
    stats_ov = _create_stats_overlay(page, base_url, name="test-stats-breakdown")
    page.request.put(
        f"{base_url}/api/overlays/{stats_ov['id']}",
        data=json.dumps(
            {"elements": {"totalCompleted": False, "breakdown": "completed"}}
        ),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{stats_ov['name']}-stats")
    expect(page.locator(".stat-line", has_text="Completed:")).to_be_visible()

    page.request.delete(f"{base_url}/api/overlays/{stats_ov['id']}")


def test_stats_overlay_breakdown_active(page: Page, base_url: str):
    stats_ov = _create_stats_overlay(page, base_url, name="test-stats-active")
    page.request.put(
        f"{base_url}/api/overlays/{stats_ov['id']}",
        data=json.dumps({"elements": {"totalCompleted": True, "breakdown": "active"}}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{stats_ov['name']}-stats")
    expect(page.locator(".stat-line", has_text="Active:")).to_be_visible()

    page.request.delete(f"{base_url}/api/overlays/{stats_ov['id']}")


def test_stats_overlay_game_filter(page: Page, base_url: str):
    hunt1 = _create_hunt(page, base_url, game="Yellow")
    hunt2 = _create_hunt(page, base_url, game="Red / Blue", name="pikachu")

    page.request.post(
        f"{base_url}/api/hunts/{hunt1['id']}/complete",
        data=json.dumps({}),
        headers={"Content-Type": "application/json"},
    )

    stats_ov = _create_stats_overlay(page, base_url, name="test-stats-game")
    page.request.put(
        f"{base_url}/api/overlays/{stats_ov['id']}",
        data=json.dumps(
            {
                "game": "Yellow",
                "elements": {"totalCompleted": False, "breakdown": "completed"},
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    page.goto(f"{base_url}/overlay/{stats_ov['name']}-stats")
    expect(
        page.locator(".stat-line", has_text="Completed: 1 / 1 total")
    ).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt1['id']}")
    page.request.delete(f"{base_url}/api/hunts/{hunt2['id']}")
    page.request.delete(f"{base_url}/api/overlays/{stats_ov['id']}")
