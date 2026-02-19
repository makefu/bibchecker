from __future__ import annotations

import copy
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask.typing import ResponseReturnValue

from bibchecker.database import save_database
from bibchecker.filters import filter_ids
from bibchecker.input import load_ids, load_user_description
from bibchecker.parsers import parse_id


@dataclass
class RefreshResult:
    """Information about the last refresh run."""

    refreshed_at: datetime
    entries: int
    output_dir: Path
    rendered_files: List[Dict[str, str]]


DEFAULT_MY_BIBS = "Bad Cannstatt,Feuerbach,Freiberg,Neugereut,Ost,Stadtbibliothek am Mailänder Platz,Zuffenhausen,Mediathek im KUBUS"


def create_app() -> Flask:
    """Create and configure the Flask application."""

    template_dir = Path(__file__).parent / "templates"
    app = Flask(__name__, template_folder=str(template_dir))

    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-secret"),
        INPUT_FILE=Path(os.environ.get("BIB_INPUT_FILE", "STUFF")).resolve(),
        OUTPUT_DIR=Path(os.environ.get("BIB_OUTPUT_DIR", "out")).resolve(),
        CACHE_FILE=Path(os.environ.get("BIB_CACHE_FILE", "out/cache.json")).resolve(),
        MY_BIBS=os.environ.get("BIBCHECKER_MYBIBS", DEFAULT_MY_BIBS),
        REFRESH_TIME=os.environ.get("BIBCHECKER_REFRESH_TIME", "04:00"),
        STATE={"last_refresh": None},
    )

    app.config["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)

    scheduler = BackgroundScheduler(daemon=True)
    _schedule_daily_refresh(app, scheduler)
    scheduler.start()
    app.config["SCHEDULER"] = scheduler

    _register_routes(app)
    return app


def _register_routes(app: Flask) -> None:
    @app.route("/", methods=["GET"])
    def dashboard() -> ResponseReturnValue:
        input_text = _load_input_text(app.config["INPUT_FILE"])
        last_refresh: Optional[RefreshResult] = app.config["STATE"].get("last_refresh")
        if last_refresh and last_refresh.rendered_files:
            generated = _sort_rendered_files(last_refresh.rendered_files)
        else:
            generated = _list_generated_files(app.config["OUTPUT_DIR"])
        return render_template(
            "dashboard.html",
            input_text=input_text,
            input_file=app.config["INPUT_FILE"],
            output_dir=app.config["OUTPUT_DIR"],
            cache_file=app.config["CACHE_FILE"],
            my_bibs=_split_bibs(app.config["MY_BIBS"]),
            refresh_time=app.config["REFRESH_TIME"],
            generated=generated,
            last_refresh=last_refresh,
        )

    @app.post("/save")
    def save_input() -> ResponseReturnValue:
        content = request.form.get("content", "")
        _save_input_text(app.config["INPUT_FILE"], content)
        flash("Input file saved.")
        return redirect(url_for("dashboard"))

    @app.post("/refresh")
    def refresh() -> ResponseReturnValue:
        result = _refresh_reports(app)
        flash(f"Reports refreshed at {result.refreshed_at:%Y-%m-%d %H:%M}.")
        return redirect(url_for("dashboard"))

    @app.get("/files/<path:filename>")
    def serve_file(filename: str) -> ResponseReturnValue:
        return send_from_directory(str(app.config["OUTPUT_DIR"]), filename, as_attachment=False)

    @app.get("/health")
    def health() -> ResponseReturnValue:
        last: Optional[RefreshResult] = app.config["STATE"].get("last_refresh")
        payload = {
            "last_refresh": last.refreshed_at.isoformat() if last else None,
            "entries": last.entries if last else None,
        }
        return jsonify(payload)


def _schedule_daily_refresh(app: Flask, scheduler: BackgroundScheduler) -> None:
    hour, minute = _parse_refresh_time(app.config["REFRESH_TIME"])

    def _job() -> None:
        with app.app_context():
            _refresh_reports(app)

    scheduler.add_job(
        _job,
        trigger=CronTrigger(hour=hour, minute=minute),
        name="bibchecker-daily-refresh",
        replace_existing=True,
    )


def _refresh_reports(app: Flask) -> RefreshResult:
    """Recreate all report files based on the current input file."""

    input_file: Path = app.config["INPUT_FILE"]
    output_dir: Path = app.config["OUTPUT_DIR"]
    cache_file: Path = app.config["CACHE_FILE"]

    output_dir.mkdir(parents=True, exist_ok=True)

    ids = list(load_ids(str(input_file)))
    entries = _parse_entries(ids)
    user_descriptions = dict(load_user_description(str(input_file)))
    for entry in entries:
        entry['user_description'] = user_descriptions[entry['id']]

    save_database(str(cache_file), entries)

    timestamp = datetime.now()
    my_bibs = _split_bibs(app.config["MY_BIBS"])
    all_bibs = _collect_bibs(entries)

    rendered_files = _write_reports(app, entries, ids, all_bibs, my_bibs, output_dir, timestamp)

    result = RefreshResult(
        refreshed_at=timestamp,
        entries=len(entries),
        output_dir=output_dir,
        rendered_files=rendered_files,
    )
    app.config["STATE"]["last_refresh"] = result
    return result


def _parse_entries(ids: Iterable[str]) -> List[Dict[str, Any]]:
    parsed: List[Dict[str, Any]] = []
    for ident in ids:
        try:
            parsed.append(parse_id(ident))
        except ValueError as exc:
            # Skip invalid IDs but keep running to produce useful output
            print(f"Skipping {ident}: {exc}")
    return parsed


def _write_reports(
    app: Flask,
    entries: List[Dict[str, Any]],
    ids: List[str],
    all_bibs: List[str],
    my_bibs: List[str],
    output_dir: Path,
    timestamp: datetime,
) -> List[Dict[str, str]]:
    rendered_files: List[Dict[str, str]] = []
    my_bibs_set = set(my_bibs)

    # Order: all-items pages first, then mybibs, then per-bib (my_bibs first), then rest
    per_bib_ordered = [b for b in all_bibs if b in my_bibs_set] + [b for b in all_bibs if b not in my_bibs_set]

    # Per-library pages (only available items)
    for bib in per_bib_ordered:
        filtered = _filtered_entries(entries, only_available=True, bibfilter=[bib])
        html = render_template(
            "report_item.html",
            title=f"{bib} (nur verfügbar)",
            subtitle="Gefiltert nach Bibliothek",
            entries=filtered,
            timestamp=timestamp,
            info_line="Nur verfügbare Exemplare",
        )
        target = output_dir / f"{bib}.html"
        target.write_text(html, encoding="utf-8")
        rendered_files.append(
            {
                "name": target.name,
                "description": f"{bib}",
                "scope": "Nur verfügbare Exemplare",
                "priority": "bib-mine" if bib in my_bibs_set else "bib-other",
            }
        )

    # My bibs summary (only available)
    my_filtered = _filtered_entries(entries, only_available=True, bibfilter=my_bibs)
    my_grouped = _group_by_bib(my_filtered)
    my_html = render_template(
        "report_bib.html",
        title="Meine Bibliotheken",
        subtitle=", ".join(my_bibs) if my_bibs else "Keine Bibliotheken definiert",
        grouped=my_grouped,
        timestamp=timestamp,
        info_line="Nur verfügbare Exemplare",
    )
    my_target = output_dir / "mybibs.html"
    my_target.write_text(my_html, encoding="utf-8")
    rendered_files.append(
        {
            "name": my_target.name,
            "description": "Meine Bibliotheken",
            "scope": "Nur verfügbare Exemplare",
            "priority": "mybibs",
        }
    )

    # All items by title
    all_items = _filtered_entries(entries, all_data=True, only_available=False)
    all_items = sorted(all_items, key=lambda e: e.get("Titel", ""))
    all_items_html = render_template(
        "report_item.html",
        title="Alle Medien (nach Titel)",
        subtitle=f"{len(ids)} IDs",  # count of IDs even if parsing failed
        entries=all_items,
        timestamp=timestamp,
        info_line="Alle Exemplare",
    )
    all_items_target = output_dir / "all_items.html"
    all_items_target.write_text(all_items_html, encoding="utf-8")
    rendered_files.append(
        {
            "name": all_items_target.name,
            "description": "Alle Medien nach Titel",
            "scope": "Alle Exemplare",
            "priority": "multi",
        }
    )

    # All items grouped by library
    all_grouped = _group_by_bib(_filtered_entries(entries, all_data=True, only_available=False))
    all_bib_html = render_template(
        "report_bib.html",
        title="Alle Medien (nach Bibliothek)",
        subtitle=f"{len(ids)} IDs",
        grouped=all_grouped,
        timestamp=timestamp,
        info_line="Alle Exemplare",
    )
    all_bib_target = output_dir / "all_bib.html"
    all_bib_target.write_text(all_bib_html, encoding="utf-8")
    rendered_files.append(
        {
            "name": all_bib_target.name,
            "description": "Alle Medien nach Bibliothek",
            "scope": "Alle Exemplare",
            "priority": "multi",
        }
    )

    # Sort according to priorities
    def _priority_key(item: Dict[str, str]) -> Tuple[int, str]:
        order = {
            "multi": 0,
            "mybibs": 1,
            "bib-mine": 2,
            "bib-other": 3,
        }
        return (order.get(item.get("priority", "bib-other"), 9), item.get("name", ""))

    rendered_files.sort(key=_priority_key)

    # Index page
    index_html = render_template(
        "report_index.html",
        title="Bibliothek Übersicht",
        timestamp=timestamp,
        generated=rendered_files,
        per_bib=per_bib_ordered,
    )
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

    return rendered_files


def _filtered_entries(
    entries: List[Dict[str, Any]],
    *,
    all_data: bool = False,
    only_available: bool = False,
    bibfilter: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    working_copy = copy.deepcopy(entries)
    return list(
        filter_ids(
            working_copy,
            all_data=all_data,
            only_available=only_available,
            bibfilter=bibfilter,
        )
    )


def _group_by_bib(entries: List[Dict[str, Any]]) -> List[Tuple[str, List[Dict[str, Any]]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for entry in entries:
        for status in entry.get("status", []):
            bib = status.get("bib", "Unbekannt")
            grouped.setdefault(bib, []).append({"entry": entry, "status": status})
    return sorted(grouped.items(), key=lambda item: item[0])


def _collect_bibs(entries: List[Dict[str, Any]]) -> List[str]:
    seen = {
        status.get("bib")
        for entry in entries
        for status in entry.get("status", [])
        if status.get("bib")
    }
    return sorted(seen)


def _split_bibs(raw: str) -> List[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def _parse_refresh_time(value: str) -> Tuple[int, int]:
    try:
        hour_str, minute_str = value.split(":", 1)
        hour, minute = int(hour_str), int(minute_str)
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError
        return hour, minute
    except Exception:
        return 4, 0


def _load_input_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _save_input_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _list_generated_files(output_dir: Path) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []
    if not output_dir.exists():
        return files
    for child in sorted(output_dir.iterdir()):
        if child.suffix.lower() != ".html":
            continue
        files.append(
            {
                "name": child.name,
                "updated": datetime.fromtimestamp(child.stat().st_mtime),
                "scope": "Unbekannt",
                "description": child.stem,
                "priority": "fallback",
            }
        )
    return _sort_rendered_files(files)


def _sort_rendered_files(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def _priority_key(item: Dict[str, Any]) -> Tuple[int, str]:
        order = {
            "multi": 0,
            "mybibs": 1,
            "bib-mine": 2,
            "bib-other": 3,
            "fallback": 4,
        }
        return (order.get(item.get("priority", "fallback"), 9), item.get("name", ""))

    return sorted(items, key=_priority_key)


app = create_app()


def main() -> None:
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
        host=os.environ.get("FLASK_HOST", "0.0.0.0"),
        port=int(os.environ.get("FLASK_PORT", "5000")),
    )


if __name__ == "__main__":
    main()
