# Bibchecker

Check availability of media at Stadtbibliothek Stuttgart and Mediathek Remseck.

## Features

- Query availability status for books, games, CDs, etc.
- Support for both Stuttgart (SAK/AK IDs) and Remseck (numeric IDs) libraries
- Output formats: plain text or HTML
- Filter by specific libraries
- Sort by item or by library
- Cache results to JSON for faster subsequent queries
- Batch processing with input files
- Automatic update of input files with fetched titles
- Web UI for editing the input file, triggering report generation, and downloading the latest reports
- Generated HTML links each title to the corresponding library catalog page (Stuttgart or Remseck)
- Daily auto-refresh (configurable) plus manual refresh endpoint/button

## Installation

### NixOS / Nix Flakes

```sh
nix build
result/bin/bibchecker SAK02068634
```

Or run directly:
```sh
nix run github:makefu/bibchecker -- SAK02068634
```

### Other OS

Install Python dependencies and run:
```sh
pip install -e .
bibchecker SAK02068634
```

## Usage

```
bibchecker [options] [IDS...]

Options:
    --all               Show all libraries even when media cannot be borrowed
    --only-available    Show books only if they are actually available
    --bib=BIB1,BIB2...  Filter for specific libraries
    --sort-by=THING     Sort by: item, bib [Default: item]
    --format=FORMAT     Output format: plain, html [Default: plain]
    -f=FILE             Input file with IDs to check
    --save-db=FILE      Save parsed data as JSON to database file
    --load-db=FILE      Load data from JSON database instead of fetching
```

### Examples

Check a single item:
```sh
bibchecker SAK02068634
```

Check items from a file and generate HTML output:
```sh
bibchecker -f mybooks.txt --format html > status.html
```

Filter for specific libraries:
```sh
bibchecker -f mybooks.txt --bib="Vaihingen,Weilimdorf" --only-available
```

Cache results for faster subsequent queries:
```sh
# Fetch and cache
bibchecker -f mybooks.txt --save-db cache.json

# Use cached data
bibchecker --load-db cache.json --format html > status.html
```

### Input File Format

```
# Comments start with hash
AK00119197

# Games section
SAK02110593 space escape
SAK02174818 zeitstrudel

# Remseck library (numeric IDs)
163581
```

- Lines starting with `#` are ignored
- IDs can be followed by optional description text
- Stuttgart IDs: `SAK...` or `AK...` (AK is auto-prefixed with S)
- Remseck IDs: numeric only (e.g., `163581`)

The input file is automatically updated with fetched titles after each run.

## Batch Processing with doall.sh

The included `doall.sh` script generates a complete HTML report with per-library pages:

```sh
result/bin/doall.sh STUFF out/
```

Arguments:
- `$1`: Input file (default: `STUFF`)
- `$2`: Output directory (default: `out`)

Generated files:
- `index.html` - Overview page with links to all reports
- `mybibs.html` - Filtered view of preferred libraries
- `all_items.html` - All media sorted by title
- `all_bib.html` - All media sorted by library
- `<LibraryName>.html` - Per-library availability reports

## Web Application (Flask)

There is a small web UI to edit the input file and trigger report generation without shell scripts.

Start the server (installs dependencies from `pyproject.toml`):

```sh
pip install -e .
bibchecker-web
# or: flask --app bibchecker.webapp run
```

Key routes and behavior:
- `/` shows the STUFF contents, lets you save edits, and provides a "refresh" button.
- `/refresh` (POST) regenerates all HTML reports using Jinja templates.
- `/files/<name>` serves the generated files from the output directory.
- A daily refresh runs automatically at 04:00 by default.

Report output (HTML):
- Overview pages first: `all_items.html` (all items by title) and `all_bib.html` (grouped by bib)
- Then `mybibs.html` (only available items for your preferred libraries)
- Then per-bibliothek pages with only available items (your preferred bibs first, then the rest)
- Each title links back to its catalog page; top meta line shows the refresh timestamp and scope ("Alle Exemplare" vs "Nur verfügbare Exemplare").

Environment variables:
- `BIB_INPUT_FILE` (default: `STUFF`)
- `BIB_OUTPUT_DIR` (default: `out`)
- `BIB_CACHE_FILE` (default: `out/cache.json`)
- `BIBCHECKER_MYBIBS` (comma-separated list; default matches `doall.sh`)
- `BIBCHECKER_REFRESH_TIME` (HH:MM, 24h; default `04:00`)
- `FLASK_HOST` / `FLASK_PORT` to adjust the bind address
- `FLASK_SECRET_KEY` to override the default dev secret

## Supported Libraries

### Stadtbibliothek Stuttgart
- ID format: `SAK...` or `AK...`
- URL: stadtbibliothek-stuttgart.de

### Mediathek Remseck
- ID format: numeric (biblionumber)
- URL: mt-remseck.lmscloud.net

## License

MIT (see LICENSE)
