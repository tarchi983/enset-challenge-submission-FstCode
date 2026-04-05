from playwright.sync_api import sync_playwright


def scrape_darija_content(url: str) -> str:
    """Explores Moroccan websites and extracts authentic Darija text from the page content."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle")
            paragraphs = page.query_selector_all('p')
            text_content = "\n".join([para.inner_text() for para in paragraphs[:10]])
            return text_content
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            browser.close()