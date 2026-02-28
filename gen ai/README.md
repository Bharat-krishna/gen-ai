# Job Scraper

Python script to scrape job postings from a public careers page and export them to an Excel file.

## Setup

From the project directory:

```bash
pip install -r requirements.txt
```

## Usage

1. Open `job_scraper.py` and update:
   - `BASE_URL` and `PAGINATED_URL_TEMPLATE` for the company's careers site.
   - CSS selectors:
     - `JOB_CARD_SELECTOR`
     - `TITLE_SELECTOR`
     - `LOCATION_SELECTOR`
     - `EXPERIENCE_SELECTOR`
     - `SALARY_SELECTOR`
     - `DEPARTMENT_SELECTOR`
     - `JOB_LINK_SELECTOR`
2. Inspect the careers page in your browser (right click → Inspect) to find the correct classes/HTML structure.
3. Run:

```bash
python job_scraper.py
```

4. The script will create an Excel file like `jobs_YYYY-MM-DD_HHMMSS.xlsx` in the current directory.

Missing fields on the page are handled gracefully and will appear as blank cells in Excel.

