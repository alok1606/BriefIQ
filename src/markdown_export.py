import re


def plain(value):
    # Strip HTML and neutralize Markdown controls in untrusted/model prose.
    return re.sub(r"([\\`*_{}\[\]<>#+!|])", r"\\\1", str(value)).replace("\n", " ")


def export_markdown(brief):
    m, w, d = brief.meeting, brief.window, brief.draft
    lines = ["# BriefIQ", "Walk Into Every Meeting Prepared", "",
             "**FIXTURE DEMO - FICTIONAL, NOT LIVE RESEARCH**" if brief.demo else "**Live research briefing**",
             f"## {plain(m.name)}", f"Meeting: {m.when.isoformat()} ({m.timezone})",
             f"Research period (UTC): {w.start.isoformat()} to {w.end.isoformat()}",
             f"Researched at: {w.researched_at.isoformat()}", f"Purpose: {plain(m.purpose or 'General preparation')}", "",
             "## Executive summary"]
    def claim(c):
        refs = " ".join(f"[{i}]" for i in c.citation_ids)
        return f"{plain(c.text)} {refs} ({'Source-backed; review excerpt' if c.evidence == 'source_backed' else 'Uncertain - verify'})"
    lines.extend("- " + claim(c) for c in d.summary)
    lines += ["", "## Key developments"]
    if not d.developments:
        lines.append("Insufficient evidence for recent developments.")
    for dev in d.developments:
        lines += ["- " + claim(dev), "  - Why it may matter (analysis): " + plain(dev.why_it_matters),
                  "  - Discuss: " + plain(dev.discussion_point)]
    lines += ["", "## Open questions", *(f"- {plain(q)}" for q in d.questions), "", "## Sources"]
    for s in brief.evidence.sources:
        lines.append(f"[{s.id}]: <{s.url}> \"{s.id}\"")
        lines.append(f"- {s.id}: [{plain(s.title)}](<{s.url}>) | {s.published or 'Publication date unknown'} | {s.date_status}")
    lines += ["", "## Uncertainty and scope", *(f"- {plain(n)}" for n in [*w.notes, *brief.evidence.notes, *d.uncertainty]),
              "- Source-backed means attributed to a retrieved excerpt, not independently verified. Identity matches require human review."]
    return "\n".join(lines) + "\n"
