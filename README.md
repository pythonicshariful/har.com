# HAR Property Scraper

Automate county-level property searches on [HAR.com](https://www.har.com/) with Selenium, `undetected_chromedriver`, and a real Brave user profile. The scraper mimics human browsing (scrolling, pacing, pagination) while exporting well-structured JSON – ready for dashboards, alerts, or downstream analysis.

---

## Highlights

- **Human-like automation** – random delays, staggered scrolls, and stealthy Selenium flags keep the session closer to real browsing.
- **Configurable at runtime** – pass filters (county, price cap, page limit, acreage/residential toggles) and networking options (IP/port) directly into `scrape_har_properties`.
- **Real Brave profile** – reuses your existing session/cookies by pointing to an on-disk profile directory.
- **Resumable runs** – optionally load and append to an existing JSON file so long scrapes survive Brave crashes or PowerShell restarts.
- **Rich property payload** – address, list price, acres (auto-converted from sq. ft.), listing URL, status, badges, agent info, DOM counter, and more.

---

## Repository Layout

| Path | Purpose |
| --- | --- |
| `main.py` | Core scraper with the `scrape_har_properties` function and helper utilities. |
| `run.py` | Minimal example showing how to call the scraper with custom arguments (imports `main.py`). |
| `requirements.txt` | Locked dependency versions for Selenium, undetected-chromedriver, and supporting packages. |
| `chromedriver.exe` | Chromium/Brave-compatible driver (replace when Brave updates). |
| `data.json` | Sample scrape output for quick schema reference. |
| `har_properties_all_pages.json` | Default output file created at runtime (not committed). |

---

## Prerequisites

| Component | Details |
| --- | --- |
| Windows 10/11 | Script is tested from PowerShell. |
| Python ≥ 3.12 | Use the included `venv` folder or a clean environment of your choice. |
| Brave Browser (stable) | [Download Brave](https://brave.com/download/), launch it once so the profile folder exists. |
| Brave profile path | Typically `C:\Users\<you>\AppData\Local\BraveSoftware\Brave-Browser\User Data`. |
| Matching Chromium driver | `chromedriver.exe` must match Brave’s Chromium version (check `brave://settings/help`). |

> **Tip:** Grab the right driver from [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) and drop it in the repo root or update the path passed to `scrape_har_properties`.

---

## First-Time Setup

1. **Clone / copy the repo to `D:\CleintProject\New` (or your preferred folder).**
2. **Install dependencies**
   ```powershell
   cd D:\CleintProject\New
   .\venv\Scripts\Activate.ps1   # optional
   pip install -r requirements.txt
   ```
3. **Update default browser paths** (if needed)  
   Edit the `DEFAULT_BROWSER_SETTINGS` dict near the top of `main.py` or pass overrides directly when calling the scraper:
   - `brave_binary` → e.g. `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe`
   - `profile_dir` → the folder reported under *Profile Path* in `brave://version`
   - `chromedriver_path` → absolute or relative path to your driver
4. **Close all Brave windows** so the profile directory is unlocked before running the script.

---

## Configuration Cheatsheet

`main.py` exposes sane defaults via `DEFAULT_FILTERS` and `DEFAULT_BROWSER_SETTINGS`, but every option can be overridden at call time:

| Argument | Type | Description |
| --- | --- | --- |
| `county` | `str` | HAR dropdown label (e.g. `"Montgomery"`, `"Harris"`). |
| `max_price` | `int` | Value sent to the "Price Max" filter; `None` leaves the filter alone. |
| `max_pages` | `int` | Safety cap to avoid infinite pagination. |
| `acreage`, `residential` | `bool` | Toggle the respective HAR checkboxes. |
| `ip`, `port` | `str`, `int` | Optional proxy endpoint (only added if both values supplied). |
| `output_filename` | `str or None` | Defaults to `har_properties_all_pages.json`; set `None` to skip disk writes and work with return values only. |
| `reuse_existing_progress` | `bool` | When true, existing JSON content is loaded and appended to (handy for resuming long scrapes). |
| Browser paths | `str` | Override `brave_binary`, `profile_dir`, `chromedriver_path` if your environment differs. |

Advanced users can tweak `build_browser_options()` to add/remove Chrome arguments. If the driver complains about the `excludeSwitches` flag, the script automatically retries with a pared-down set of options.

---

## Running the Scraper

### Quick start (uses defaults)
```powershell
python main.py
```

### Custom run via helper script
Example `run.py` invocation (ships in the repo):

```python
from main import scrape_har_properties

scrape_har_properties(
    county="Harris",
    max_price=35_000,
    max_pages=5,
    acreage=False,
    residential=True,
    output_filename=None,  # return data without touching disk
)
```

You can duplicate `run.py` for different presets or integrate the function into a larger pipeline. The function returns a `list[dict]`, so you can load results straight into Pandas or another datastore.

During execution you’ll see:

- Selected filters and derived settings (e.g., page cap, output path).
- Per-page card counts, running totals, and acres coverage stats.
- Friendly emoji markers for navigation, saving, and retry behavior.

If an error occurs mid-run, whatever has already been collected is persisted (when `output_filename` is set) before the exception bubbles up.

---

## Output & Data Model

- **Default file**: `har_properties_all_pages.json` (UTF‑8, pretty printed).  
- **Schema sample**: see `data.json`. Each property contains:
  - `address`, `price`, `listing_url`
  - `acres` (auto-computed from lot or interior square footage when possible)
  - `additional_info`
    - `status`, `description`
    - `features`: bedrooms, bathrooms, square footage, lot size, stories, etc.
    - `badges`: e.g., “Just Listed”, “Price Reduction”
    - `agent_info`: agent + broker names
    - `photo_count`, `days_on_market`

Because `ensure_ascii=False` is used, HAR’s native characters (accents, etc.) are preserved.

---

## Troubleshooting & Tips

- **Driver mismatch**  
  After every Brave update, grab the matching Chromium driver; mismatches usually manifest as “This version of ChromeDriver only supports…” errors.

- **Profile in use**  
  Close Brave completely (check Task Manager). Selenium cannot attach to a locked profile directory.

- **HAR rate limits / CAPTCHA**  
  Occasionally HAR will block automation. Handle the challenge manually in the launched Brave window and continue; the script is patient and will keep polling.

- **Pagination stalls**  
  The script checks for disabled "Next" buttons and safely stops when no more pages exist or when `max_pages` is hit.

- **Proxy usage**  
  Supply both `ip` and `port` to route Brave traffic through a proxy. Leave them `None` for direct connections.

---

## Extending the Tool

- Pipe the returned list into analytics notebooks or dashboards (Pandas/Polars).
- Swap Brave for another Chromium-based browser by pointing `brave_binary` to a different executable.
- Schedule recurring runs with Task Scheduler, wrapping `run.py` presets or custom orchestration scripts.
- Add new filters: replicate the interaction pattern in `main.py` and toggle via extra keyword arguments.

Feel free to open issues or PRs with improvements, new filter hooks, or multi-threaded experiments. Happy scraping! 💪