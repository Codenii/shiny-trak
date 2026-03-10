import json

from playwright.sync_api import Page, expect


def test_settings_panel_opens(page: Page, base_url: str):
    page.goto(base_url)
    page.get_by_role("button", name="Settings").click()
    expect(page.get_by_text("When closing the window")).to_be_visible()
    expect(page.get_by_text("When marking a hunt as found")).to_be_visible()
    expect(page.locator("input[name='close_behavior']").first).to_be_visible()
    expect(page.locator("input[name='mark_found_behavior']").first).to_be_visible()


def test_settings_close_behavior_saved(page: Page, base_url: str):
    page.goto(base_url)
    page.get_by_role("button", name="Settings").click()

    with page.expect_response(
        lambda r: "/api/settings" in r.url and r.request.method == "PUT"
    ):
        page.locator("input[name='close_behavior'][value='minimize']").click()

    resp = page.request.get(f"{base_url}/api/settings")
    assert resp.json()["close_behavior"] == "minimize"

    # Restore
    with page.expect_response(
        lambda r: "/api/settings" in r.url and r.request.method == "PUT"
    ):
        page.locator("input[name='close_behavior'][value='ask']").click()


def test_settings_mark_found_behavior_saved(page: Page, base_url: str):
    page.goto(base_url)
    page.get_by_role("button", name="Settings").click()

    with page.expect_response(
        lambda r: "/api/settings" in r.url and r.request.method == "PUT"
    ):
        page.locator("input[name='mark_found_behavior'][value='never']").click()

    resp = page.request.get(f"{base_url}/api/settings")
    assert resp.json()["mark_found_behavior"] == "never"

    # Restore
    with page.expect_response(
        lambda r: "/api/settings" in r.url and r.request.method == "PUT"
    ):
        page.locator("input[name='mark_found_behavior'][value='ask']").click()


def test_settings_persist_across_reload(page: Page, base_url: str):
    page.request.put(
        f"{base_url}/api/settings",
        data=json.dumps({"close_behavior": "quit", "mark_found_behavior": "never"}),
        headers={"Content-Type": "application/json"},
    )

    page.goto(base_url)
    with page.expect_response(
        lambda r: "/api/settings" in r.url and r.request.method == "GET"
    ):
        page.reload()
    page.get_by_role("button", name="Settings").click()

    expect(page.locator("input[name='close_behavior'][value='quit']")).to_be_checked()
    expect(
        page.locator("input[name='mark_found_behavior'][value='never']")
    ).to_be_checked()

    # Restore
    page.request.put(
        f"{base_url}/api/settings",
        data=json.dumps({"close_behavior": "ask", "mark_found_behavior": "ask"}),
        headers={"Content-Type": "application/json"},
    )
