from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://127.0.0.1:5000/")
    page.wait_for_timeout(1000)

    # Assert basic elements are present
    assert page.locator("h1", has_text="Origami AI Tutor").is_visible()

    # Start Camera Button
    start_btn = page.locator("#start-btn")
    assert start_btn.is_visible()

    # Feedback button should be disabled initially
    feedback_btn = page.locator("#feedback-btn")
    assert feedback_btn.is_visible()
    assert feedback_btn.is_disabled()

    # Screenshot of the initial page state
    page.screenshot(path="verification_index.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        context = browser.new_context(record_video_dir="videos", permissions=["camera"])
        page = context.new_page()
        try:
            run_cuj(page)
            print("Tests passed successfully.")
        finally:
            context.close()
            browser.close()