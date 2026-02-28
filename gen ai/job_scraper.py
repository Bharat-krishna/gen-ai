import time
from datetime import datetime
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup, Tag
import pandas as pd


"""
Generic job scraper for a company's public careers page.

This file is PRE-CONFIGURED to work against the public
training site `https://realpython.github.io/fake-jobs/`
so you can run it immediately and see results.

HOW TO USE / CUSTOMIZE
----------------------
1. Run it as-is to scrape the fake jobs site:

       pip install -r requirements.txt
       python job_scraper.py

   It will save an Excel file like: jobs_2026-02-28_153000.xlsx

2. To point it at a real company's careers page, change:
   - BASE_URL and PAGINATED_URL_TEMPLATE
   - JOB_CARD_SELECTOR
   - TITLE_SELECTOR
   - COMPANY_SELECTOR
   - LOCATION_SELECTOR
   - EXPERIENCE_SELECTOR
   - SALARY_SELECTOR
   - DEPARTMENT_SELECTOR
   - DATE_POSTED_SELECTOR
   - JOB_LINK_SELECTOR
"""


# ------------ CONFIGURATION ------------

# The first careers page URL (normally page 1)
# For this demo, we use Real Python's fake jobs site:
# https://realpython.github.io/fake-jobs/
BASE_URL = "https://realpython.github.io/fake-jobs/"

# If the site uses page numbers like ?page=1, ?page=2, etc, adapt this.
# For the fake-jobs site, everything is on one page, so we leave this empty.
PAGINATED_URL_TEMPLATE: str = ""

# Delay between requests (seconds) to be polite and reduce blocking risk
REQUEST_DELAY_SECONDS = 1.0

# HTTP headers to look more like a real browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# CSS selectors – CHANGE THESE for your target site
#
# For the fake-jobs site, each job card looks like:
# <div class="card-content">
#   <h2 class="title">Job Title</h2>
#   <h3 class="company">Company Name</h3>
#   <p class="location">City, ST</p>
#   <time datetime="2021-04-08">2021-04-08</time>
#   ...
#   <a class="card-footer-item" href="...">Apply</a>
# </div>
JOB_CARD_SELECTOR = "div.card-content"   # selector for each job listing container
TITLE_SELECTOR = "h2.title"              # inside a card
COMPANY_SELECTOR = "h3.company"          # inside a card
LOCATION_SELECTOR = "p.location"         # inside a card
EXPERIENCE_SELECTOR = ""                 # not available on fake-jobs site
SALARY_SELECTOR = ""                     # not available on fake-jobs site
DEPARTMENT_SELECTOR = ""                 # not available on fake-jobs site
DATE_POSTED_SELECTOR = "time"            # inside a card
JOB_LINK_SELECTOR = "a.card-footer-item" # link to the job detail page (relative or absolute URL)

# Limit how many jobs we keep in the final Excel.
# Set to a small number (e.g. 20) to look more "hand-picked".
# Set to None to keep all scraped jobs.
MAX_JOBS_TO_SAVE: Optional[int] = 25


# ------------ SCRAPING HELPERS ------------

def fetch_page(url: str, params: Optional[dict] = None) -> Optional[requests.Response]:
    """Fetch a page with basic error handling."""
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        return resp
    except requests.RequestException as exc:
        print(f"[ERROR] Failed to fetch {url}: {exc}")
        return None


def _safe_text(parent: Tag, selector: str) -> Optional[str]:
    """Return stripped text for the first element matching selector, or None."""
    if not selector:
        return None
    el = parent.select_one(selector)
    return el.get_text(strip=True) if el else None


def parse_job_card(card: Tag) -> Dict[str, Optional[str]]:
    """
    Extract job information from a single job card element.

    Any field that cannot be found is returned as None.
    """
    title = _safe_text(card, TITLE_SELECTOR)
    company = _safe_text(card, COMPANY_SELECTOR)
    location = _safe_text(card, LOCATION_SELECTOR)
    experience = _safe_text(card, EXPERIENCE_SELECTOR)
    salary = _safe_text(card, SALARY_SELECTOR)
    department = _safe_text(card, DEPARTMENT_SELECTOR)
    date_posted = _safe_text(card, DATE_POSTED_SELECTOR)

    job_link_el = card.select_one(JOB_LINK_SELECTOR) if JOB_LINK_SELECTOR else None
    job_url = job_link_el.get("href") if job_link_el else None

    return {
        "Job Title": title,
        "Company": company,
        "Location": location,
        "Experience": experience,
        "Salary": salary,
        "Department": department,
        "Date Posted": date_posted,
        "Job URL": job_url,
    }


def parse_jobs_from_html(html: str) -> List[Dict[str, Optional[str]]]:
    """Parse all job cards from a careers page HTML string."""
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(JOB_CARD_SELECTOR) if JOB_CARD_SELECTOR else []
    if not cards:
        print("[INFO] No job cards found on this page (check JOB_CARD_SELECTOR).")
    jobs = [parse_job_card(card) for card in cards]
    print(f"[INFO] Parsed {len(jobs)} job(s) from page.")
    return jobs


def crawl_all_jobs() -> List[Dict[str, Optional[str]]]:
    """
    Crawl all job pages.

    If PAGINATED_URL_TEMPLATE is empty, just fetch BASE_URL once.
    Otherwise, use simple page-number-based pagination:
    - Request page 1, 2, 3, ... using PAGINATED_URL_TEMPLATE
    - Stop when a page returns zero job cards or a request fails
    """
    all_jobs: List[Dict[str, Optional[str]]] = []

    if not PAGINATED_URL_TEMPLATE:
        print(f"[INFO] Fetching base URL: {BASE_URL}")
        resp = fetch_page(BASE_URL)
        if resp is None:
            print("[INFO] Stopping crawl due to fetch error.")
            return all_jobs
        return parse_jobs_from_html(resp.text)

    page = 1
    while True:
        url = PAGINATED_URL_TEMPLATE.format(page=page)
        print(f"[INFO] Fetching page {page}: {url}")
        resp = fetch_page(url)

        if resp is None:
            print("[INFO] Stopping crawl due to fetch error.")
            break

        page_jobs = parse_jobs_from_html(resp.text)
        if not page_jobs:
            print("[INFO] No jobs on this page. Assuming end of listings.")
            break

        all_jobs.extend(page_jobs)
        print(f"[INFO] Total jobs collected so far: {len(all_jobs)}")

        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return all_jobs


# ------------ EXPORT TO EXCEL ------------

def save_jobs_to_excel(jobs: List[Dict[str, Optional[str]]], filename: Optional[str] = None) -> str:
    """Save the scraped jobs to an Excel file and return the file path."""
    if not filename:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"jobs_{timestamp}.xlsx"

    if not jobs:
        print("[WARN] No jobs to save – Excel file will not be created.")
        return filename

    # Optionally limit how many jobs we keep, to look more "human sized"
    if MAX_JOBS_TO_SAVE is not None and len(jobs) > MAX_JOBS_TO_SAVE:
        print(f"[INFO] Limiting jobs from {len(jobs)} to {MAX_JOBS_TO_SAVE} for export.")
        jobs = jobs[:MAX_JOBS_TO_SAVE]

    df = pd.DataFrame(jobs)
    df.to_excel(filename, index=False)
    print(f"[INFO] Saved {len(jobs)} job(s) to {filename}")
    return filename


def main() -> None:
    print("[INFO] Starting job scrape...")
    jobs = crawl_all_jobs()

    if not jobs:
        print("[WARN] No jobs scraped. Check the URL, selectors, and pagination logic.")
        return

    save_jobs_to_excel(jobs)


if __name__ == "__main__":
    main()

