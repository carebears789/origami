from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://127.0.0.1:5000/")
    page.wait_for_timeout(1000)

    # Go to student view
    page.get_by_role("link", name="Go to Student View").click()
    page.wait_for_timeout(1000)

    # Go back
    page.get_by_role("link", name="Back to Admin View").click()
    page.wait_for_timeout(1000)

    # Click Add New Origami
    page.get_by_role("link", name="Add New Origami").click()
    page.wait_for_timeout(1000)

    # Fill form
    page.locator("#name").fill("paper-crane")
    page.get_by_role("button", name="Create").click()
    page.wait_for_timeout(1000)

    # Click Edit on paper-crane
    page.get_by_role("link", name="Edit").click()
    page.wait_for_timeout(1000)

    # Screenshot of edit page
    page.screenshot(path="verification_edit.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="videos")
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
