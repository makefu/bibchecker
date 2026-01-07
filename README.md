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
pip install beautifulsoup4 requests docopt
python setup.py develop
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

## Supported Libraries

### Stadtbibliothek Stuttgart
- ID format: `SAK...` or `AK...`
- URL: stadtbibliothek-stuttgart.de

### Mediathek Remseck
- ID format: numeric (biblionumber)
- URL: mt-remseck.lmscloud.net

## License

MIT (see LICENSE)
