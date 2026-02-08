"""Output formatters for bibchecker."""
from datetime import datetime
from typing import Dict, Any, List, Iterable


def plain_print(iddata: Iterable[Dict[str, Any]], all_ids: List[str], sort_by: str = "item") -> None:
    """Print results in plain text format."""
    if sort_by == "item":
        _print_by_item(iddata)
    elif sort_by == "bib":
        _print_by_library(iddata, all_ids)


def _print_by_item(iddata: Iterable[Dict[str, Any]]) -> None:
    """Print results grouped by item."""
    for entry in iddata:
        try:
            print()
            print(f"{entry['Titel']}")
        except Exception:
            print(f"!! problem with {entry}")
            continue

        for av in entry["status"]:
            print(f"  {av.get('bib')} ({av.get('standort') or 'No Data'}) - {av.get('available')}")


def _print_by_library(iddata: Iterable[Dict[str, Any]], all_ids: List[str]) -> None:
    """Print results grouped by library."""
    print(f"Gathering {len(all_ids)} entries first ... please wait")
    bib_entries: Dict[str, List[Dict[str, Any]]] = {}

    for ident, entry in enumerate(iddata):
        print(ident, end=" ", flush=True)
        for status in entry["status"]:
            status["entry"] = entry
            bib = status.get("bib", "Unknown")
            if bib not in bib_entries:
                bib_entries[bib] = []
            bib_entries[bib].append(status)

    print("done")
    for k, vals in bib_entries.items():
        print()
        print(f"Library '{k}'")
        for v in vals:
            entry = v["entry"]
            print(f"  {entry['Titel']} - {v.get('standort')} - {v.get('available')}")


def html_print(iddata: Iterable[Dict[str, Any]], all_ids: List[str], sort_by: str = "item") -> None:
    """Print results in HTML format."""
    html_parts: List[str] = [_html_header()]

    if sort_by == "item":
        html_parts.extend(_html_by_item(iddata))
    elif sort_by == "bib":
        html_parts.extend(_html_by_library(iddata))

    html_parts.append(_html_footer())
    print("".join(html_parts))


def _html_header() -> str:
    """Generate HTML header with CSS."""
    return """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Bibliothek Status</title>
    <style>
        body { font-family: system-ui, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #333; margin-bottom: 15px; }
        table { border-collapse: collapse; width: 100%; background: white; }
        th { background: #eee; text-align: left; padding: 8px; border-bottom: 2px solid #999; }
        td { padding: 6px 8px; border-bottom: 1px solid #eee; vertical-align: top; }
        .title { font-weight: 600; background: #fafafa; border-top: 2px solid #666; }
        .first { border-top: 2px solid #666; }
        .ok { color: #228b22; font-weight: 600; }
        .no { color: #dc143c; }
        .loc { color: #888; font-size: 0.9em; }
        .ts { color: #999; font-size: 0.8em; margin-top: 20px; }
    </style>
</head>
<body>
<h1>Bibliothek Status</h1>
<table>
<tr><th>Titel</th><th>Bibliothek</th><th>Standort</th><th>Status</th></tr>
"""


def _html_footer() -> str:
    """Generate HTML footer with timestamp."""
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    return f'</table>\n<div class="ts">Stand: {timestamp}</div>\n</body></html>'


def _html_by_item(iddata: Iterable[Dict[str, Any]]) -> List[str]:
    """Generate HTML rows grouped by item."""
    parts: List[str] = []
    for entry in iddata:
        title = entry.get("Titel", "Unbekannt")
        catalog_url = entry.get("catalog_url")
        statuses = entry.get("status", [])
        if statuses:
            for i, av in enumerate(statuses):
                bib = av.get("bib", "?")
                loc = av.get("standort") or "-"
                avail = av.get("available", "?")
                cls = "ok" if av.get("can_be_borrowed") else "no"
                if i == 0:
                    parts.append(
                        f'<tr><td class="title" rowspan="{len(statuses)}"><a href="{catalog_url}">{title}</a></td>'
                        f'<td class="first">{bib}</td><td class="first loc">{loc}</td>'
                        f'<td class="first {cls}">{avail}</td></tr>\n'
                    )
                else:
                    parts.append(
                        f'<tr><td>{bib}</td><td class="loc">{loc}</td>'
                        f'<td class="{cls}">{avail}</td></tr>\n'
                    )
        else:
            parts.append(
                f'<tr><td class="title"><a href="{catalog_url}">{title}</a></td>'
                f'<td colspan="3" class="first no">Keine Daten</td></tr>\n'
            )
    return parts


def _html_by_library(iddata: Iterable[Dict[str, Any]]) -> List[str]:
    """Generate HTML rows grouped by library."""
    parts: List[str] = []
    bib_entries: Dict[str, List[Dict[str, Any]]] = {}

    for entry in iddata:
        for status in entry["status"]:
            status["entry"] = entry
            bib = status.get("bib", "Unbekannt")
            if bib not in bib_entries:
                bib_entries[bib] = []
            bib_entries[bib].append(status)

    for library, items in sorted(bib_entries.items()):
        parts.append(
            f'<tr><td colspan="4" style="background:#ddd;font-weight:600;padding:10px;">'
            f'{library}</td></tr>\n'
        )
        for item in items:
            entry = item.get("entry", {})
            title = entry.get("Titel", "Unbekannt")
            catalog_url = entry.get("catalog_url")
            loc = item.get("standort") or "-"
            avail = item.get("available", "?")
            cls = "ok" if item.get("can_be_borrowed") else "no"
            parts.append(
                f'<tr><td class="title"><a href="{catalog_url}">{title}</a></td><td>-</td>'
                f'<td class="loc">{loc}</td><td class="{cls}">{avail}</td></tr>\n'
            )
    return parts
