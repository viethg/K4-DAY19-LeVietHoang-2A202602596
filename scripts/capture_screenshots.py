import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def capture():
    img_dir = Path("report/img")
    img_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        print("Navigating to http://localhost:7474 ...")
        page.goto("http://localhost:7474/browser/")
        page.wait_for_timeout(3000)

        # Check if login form is present
        try:
            page.wait_for_selector('input[type="password"]', timeout=5000)
            pwd = page.locator('input[type="password"]').first
            if pwd.is_visible():
                print("Logging into Neo4j Browser...")
                pwd.fill("password123")
                pwd.press("Enter")
                page.wait_for_timeout(4000)
        except Exception:
            pass

        # Dismiss tooltip/tour if present
        try:
            page.wait_for_selector('.ndl-modal-root', state='hidden', timeout=6000)
        except Exception:
            pass
        dismiss_btn = page.locator('button:has-text("Dismiss"), button:has-text("Close")')
        if dismiss_btn.count() > 0:
            try:
                dismiss_btn.first.click()
                page.wait_for_timeout(1000)
            except Exception:
                pass

        # Helper to run a command in the Neo4j editor
        def run_cypher(query: str, wait_sec: float = 3.0):
            # Click editor area
            editor = page.locator('.view-lines, [role="textbox"], textarea, .monaco-editor').first
            editor.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.type(query)
            page.keyboard.press("Control+Enter")
            page.wait_for_timeout(int(wait_sec * 1000))

        # Clear any previous frames
        run_cypher(":clear", 1.5)

        # 1. Q-A: Count nodes by label
        query_a = "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC;"
        run_cypher(query_a, 3.0)
        # Switch to Table view if not already
        table_btn = page.locator('button[title*="table" i], [aria-label*="table" i], button:has-text("Table")')
        if table_btn.count() > 0:
            try:
                table_btn.first.click()
                page.wait_for_timeout(1000)
            except Exception:
                pass
        shot_a = img_dir / "kg_count.png"
        page.screenshot(path=str(shot_a), full_page=False)
        print(f"Saved {shot_a}")

        # Clear
        run_cypher(":clear", 1.5)

        # 2. Q-B: Cross-KB bridge
        query_b = "MATCH p=(:Person)-[:INVOLVED_IN]->(:Case)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(:Article) RETURN p LIMIT 25;"
        run_cypher(query_b, 4.0)
        # Ensure Graph view
        graph_btn = page.locator('button[title*="graph" i], [aria-label*="graph" i], button:has-text("Graph")')
        if graph_btn.count() > 0:
            try:
                graph_btn.first.click()
                page.wait_for_timeout(1000)
            except Exception:
                pass
        shot_b = img_dir / "kg_cross_kb.png"
        page.screenshot(path=str(shot_b), full_page=False)
        print(f"Saved {shot_b}")

        # Clear
        run_cypher(":clear", 1.5)

        # 3. Q-D: My case (Trần Minh Tâm)
        query_d = "MATCH p=(:Person {name:'Trần Minh Tâm'})-[:INVOLVED_IN]->(k:Case)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(:Article) OPTIONAL MATCH q=(k)-[:INVOLVES|LOCATED_IN]->() RETURN p, q;"
        run_cypher(query_d, 4.0)
        if graph_btn.count() > 0:
            try:
                graph_btn.first.click()
                page.wait_for_timeout(1000)
            except Exception:
                pass
        shot_d = img_dir / "kg_my_case.png"
        page.screenshot(path=str(shot_d), full_page=False)
        print(f"Saved {shot_d}")

        browser.close()
        print("All 3 screenshots captured successfully!")

if __name__ == "__main__":
    capture()
