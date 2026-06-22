"""Portfolio HTML -> PDF renderer.

Usage:
    pip install playwright
    playwright install chromium
    python render.py
"""
from playwright.sync_api import sync_playwright
import os

HTML = os.path.abspath(os.path.join(os.path.dirname(__file__), "portfolio.html"))
PDF = os.path.abspath(os.path.join(os.path.dirname(__file__), "portfolio.pdf"))

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"file://{HTML}")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)  # font load buffer
    page.pdf(
        path=PDF,
        format="A4",
        print_background=True,
        margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        prefer_css_page_size=True,
    )
    browser.close()

print(f"OK -> {PDF}")
print(f"   size: {os.path.getsize(PDF) / 1024:.1f} KB")
