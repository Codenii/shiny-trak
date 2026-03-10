import csv
import json
import os

from playwright.sync_api import Page, expect


def _create_hunt(page, base_url, pokemon="rattata", display_name="Rattata"):
    r = page.request.post(
        f"{base_url}/api/hunts",
        data=json.dumps(
            {
                "pokemon": pokemon,
                "displayName": display_name,
                "spriteUrl": None,
                "game": None,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    return r.json()


def _complete_hunt(page, base_url, hunt_id):
    page.request.post(
        f"{base_url}/api/hunts/{hunt_id}/complete",
        data=json.dumps({}),
        headers={"Content-Type": "application/json"},
    )


def test_export_json_all(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)

    resp = page.request.get(f"{base_url}/api/export?scope=all&format=json")
    result = resp.json()
    assert result["ok"] is True

    import store

    written = os.path.join(store.DOWNLOAD_DIR, result["filename"])
    assert os.path.exists(written)

    with open(written) as f:
        data = json.load(f)
    assert any(h["id"] == hunt["id"] for h in data)

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_export_csv_all(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)

    resp = page.request.get(f"{base_url}/api/export?scope=all&format=csv")
    result = resp.json()
    assert result["ok"] is True

    import store

    written = os.path.join(store.DOWNLOAD_DIR, result["filename"])
    assert os.path.exists(written)

    with open(written, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert any(r["displayName"] == hunt["displayName"] for r in rows)

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_export_scope_active_only(page: Page, base_url: str):
    active = _create_hunt(page, base_url, "rattata", "Rattata")
    completed = _create_hunt(page, base_url, "pidgey", "Pidgey")
    _complete_hunt(page, base_url, completed["id"])

    resp = page.request.get(f"{base_url}/api/export?scope=active&format=json")
    result = resp.json()
    assert result["ok"] is True

    import store

    with open(os.path.join(store.DOWNLOAD_DIR, result["filename"])) as f:
        data = json.load(f)

    ids = [h["id"] for h in data]
    assert active["id"] in ids
    assert completed["id"] not in ids

    page.request.delete(f"{base_url}/api/hunts/{active['id']}")
    page.request.delete(f"{base_url}/api/hunts/{completed['id']}")


def test_export_scope_completed_only(page: Page, base_url: str):
    active = _create_hunt(page, base_url, "rattata", "Rattata")
    completed = _create_hunt(page, base_url, "pidgey", "Pidgey")
    _complete_hunt(page, base_url, completed["id"])

    resp = page.request.get(f"{base_url}/api/export?scope=completed&format=json")
    result = resp.json()
    assert result["ok"] is True

    import store

    with open(os.path.join(store.DOWNLOAD_DIR, result["filename"])) as f:
        data = json.load(f)

    ids = [h["id"] for h in data]
    assert completed["id"] in ids
    assert active["id"] not in ids

    page.request.delete(f"{base_url}/api/hunts/{active['id']}")
    page.request.delete(f"{base_url}/api/hunts/{completed['id']}")


def test_export_modal_opens(page: Page, base_url: str):
    page.goto(base_url)
    page.get_by_role("button", name="Export").click()
    expect(page.get_by_text("Export Hunts")).to_be_visible()
    expect(page.locator("input[name='export_scope']").first).to_be_visible()
    expect(page.locator("input[name='export_format']").first).to_be_visible()


def test_export_toast_appears(page: Page, base_url: str):
    hunt = _create_hunt(page, base_url)
    page.goto(base_url)
    page.get_by_role("button", name="Export").click()

    with page.expect_response(
        lambda r: "/api/export" in r.url and r.request.method == "GET"
    ):
        page.get_by_role("button", name="Download").click()

    expect(page.get_by_text("Saved to Downloads/")).to_be_visible()

    page.request.delete(f"{base_url}/api/hunts/{hunt['id']}")


def test_export_scope_all_includes_both(page: Page, base_url: str):
    active = _create_hunt(page, base_url, "rattata", "Rattata")
    completed = _create_hunt(page, base_url, "pidgey", "Pidgey")
    _complete_hunt(page, base_url, completed["id"])

    resp = page.request.get(f"{base_url}/api/export?scope=all&format=json")
    result = resp.json()
    assert result["ok"] is True

    import store

    with open(os.path.join(store.DOWNLOAD_DIR, result["filename"])) as f:
        data = json.load(f)

    ids = [h["id"] for h in data]
    assert active["id"] in ids
    assert completed["id"] in ids

    page.request.delete(f"{base_url}/api/hunts/{active['id']}")
    page.request.delete(f"{base_url}/api/hunts/{completed['id']}")
