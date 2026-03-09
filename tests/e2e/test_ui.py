from playwright.sync_api import Page, expect


def test_control_panel_loads(page: Page, base_url: str):
    page.goto(base_url)
    expect(page).to_have_title("Shiny Trak")
    expect(page.get_by_placeholder("Search Pokemon...")).to_be_visible()
    expect(page.get_by_text("Hunts", exact=True)).to_be_visible()
    expect(page.get_by_text("History", exact=True)).to_be_visible()


def test_add_hunt(page: Page, base_url: str):
    page.goto(base_url)
    page.get_by_placeholder("Search Pokemon...").fill("pikachu")
    page.get_by_role("button", name="Add Hunt").click()
    expect(page.get_by_text("Pikachu", exact=True).first).to_be_visible(timeout=15000)


def test_increment_decrement(page: Page, base_url: str):
    page.goto(base_url)
    expect(page.get_by_text("Pikachu", exact=True).first).to_be_visible()

    page.get_by_role("button", name="+", exact=True).first.click()
    resp = page.request.get(f"{base_url}/api/hunts")
    pikachu = next(h for h in resp.json() if h["pokemon"] == "pikachu")
    assert pikachu["count"] == 1

    page.get_by_role("button", name="-", exact=True).first.click()
    resp = page.request.get(f"{base_url}/api/hunts")
    pikachu = next(h for h in resp.json() if h["pokemon"] == "pikachu")
    assert pikachu["count"] == 0


def test_mark_as_found(page: Page, base_url: str):
    page.goto(base_url)
    expect(page.get_by_text("Pikachu", exact=True).first).to_be_visible()

    page.locator("button[title='Mark as Found']").click()
    expect(
        page.get_by_placeholder("How did you find it? Any thoughts...")
    ).to_be_visible()
    page.get_by_role("button", name="Mark as Found").last.click()

    page.get_by_text("History", exact=True).click()
    expect(page.get_by_text("Pikachu", exact=True).first).to_be_visible()


def test_overlay_renders(page: Page, base_url: str):
    page.goto(f"{base_url}/overlay/main")
    expect(page.locator("#hunts")).to_be_attached()
