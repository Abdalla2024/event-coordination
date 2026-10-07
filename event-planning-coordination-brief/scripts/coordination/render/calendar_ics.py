"""event-calendar.ics: a draft calendar (METHOD:PUBLISH) of tentative, transparent planning blocks.

Emitted only for scheduling blocks supported by the model: the event window, the run-of-show blocks
(buffers excluded), the accessibility walkthrough and the rehearsal. Deadlines and the venue-hold
expiry are plan items, not events. No attendees, no organizer. A blocked run or a run with no viable
option produces an empty, valid calendar.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

TAIPEI = timezone(timedelta(hours=8))
TZID = "Asia/Taipei"
DOMAIN = "event-planning-coordination-brief"
BANNER = "PROPOSED - NOT BOOKED OR CONFIRMED."


def _esc(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n"))


def _fold(line: str) -> list[str]:
    """RFC 5545 folding at 75 octets without splitting a UTF-8 character."""
    out, cur, size = [], "", 0
    for ch in line:
        n = len(ch.encode("utf-8"))
        if size + n > (75 if not out else 74):
            out.append(cur)
            cur, size = "", 0
        cur += ch
        size += n
    out.append(cur)
    return [out[0]] + [" " + x for x in out[1:]]


def _local(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(TAIPEI).strftime("%Y%m%dT%H%M%S")


def _stamp(iso: str) -> str:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def events(view: dict) -> list[dict]:
    if view["run"]["status"] == "blocked" or view["recommendation"]["status"] == "no-viable-option":
        return []
    conditions = sorted({f"{c['type']} ({', '.join(c['owners']) or 'owner not stated'})"
                         for cs in view["recommendation"]["conditions"].values() for c in cs})
    cond_text = ("Open conditions: " + "; ".join(conditions) + ".") if conditions else "Open conditions: none recorded."
    out = []
    w = view["window"]
    if w:
        out.append({"uid": f"B-event-window-{w['date'].replace('-', '')}", "summary": "Demo Day programme window",
                    "start": w["start"], "end": w["end"], "basis": "source (calendar preferred event window)",
                    "extra": cond_text, "evidence": ["B-event-window"]})
    prog = view["programme"]
    for b in prog["blocks"] if prog["status"] == "planned" else []:
        if b["kind"] == "buffer":
            continue
        basis = {"source": "source", "planner-decision": "Programme planner decision (pending Programme review)",
                 "source-duration, planner-placement": "source duration; placement is a Programme planner decision"}[b["basis"]]
        out.append({"uid": f"{b['id']}-{prog['date'].replace('-', '')}", "summary": b["label"],
                    "start": b["start"], "end": b["end"], "basis": basis, "extra": cond_text,
                    "evidence": b["evidence_ids"] + b["decision_ids"]})
    for key, label in (("walkthrough", "Accessibility walkthrough"), ("rehearsal", "Rehearsal window")):
        c = view[key]
        if c and c["support"] == "supported":
            facts = c.get("note_facts", {})
            extra = []
            if facts.get("requires_venue_confirmation_first"):
                extra.append("Venue confirmation is required first.")
            if facts.get("remote_backup_acceptable"):
                extra.append("Remote backup acceptable.")
            if c["value"]["priority"] == "soft":
                extra.append("Soft constraint.")
            out.append({"uid": f"{c['value']['constraint_id']}-{c['value']['start_at'][:10].replace('-', '')}",
                        "summary": label, "start": c["value"]["start_at"], "end": c["value"]["end_at"],
                        "basis": f"source (calendar {c['value']['constraint_id']}, owner {c['value']['owner']})",
                        "extra": " ".join(extra) or "No additional calendar notes.", "evidence": [c["id"]]})
    return out


def render(view: dict) -> str:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//Quillhaven Academy//{DOMAIN}//EN", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", "X-WR-CALNAME:Demo Day planning draft (tentative)",
             "BEGIN:VTIMEZONE", f"TZID:{TZID}", "BEGIN:STANDARD", "DTSTART:19700101T000000",
             "TZOFFSETFROM:+0800", "TZOFFSETTO:+0800", "TZNAME:CST", "END:STANDARD", "END:VTIMEZONE"]
    stamp = _stamp(view["run"]["rendered_at"])
    for e in events(view):
        desc = (f"{BANNER} Draft planning block from run {view['run']['run_id']} (run status "
                f"{view['run']['status']}; recommendation {view['recommendation']['status']}). Basis: {e['basis']}. "
                f"{e['extra']} Evidence: {', '.join(e['evidence'])}.")
        lines += ["BEGIN:VEVENT", f"UID:{e['uid']}@{DOMAIN}", f"DTSTAMP:{stamp}",
                  f"DTSTART;TZID={TZID}:{_local(e['start'])}", f"DTEND;TZID={TZID}:{_local(e['end'])}",
                  f"SUMMARY:{_esc('[Tentative draft] ' + e['summary'])}", f"DESCRIPTION:{_esc(desc)}",
                  "STATUS:TENTATIVE", "TRANSP:TRANSPARENT", "CATEGORIES:PLANNING-DRAFT", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "".join(x + "\r\n" for line in lines for x in _fold(line))
