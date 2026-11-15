from .models import Draft, Claim, Development
from .utils import BriefIQError


def validate_draft(draft, evidence):
    sources = {s.id: s for s in evidence.sources}
    for claim in [*draft.summary, *draft.developments]:
        if any(i not in sources for i in claim.citation_ids):
            raise BriefIQError("The model cited a source that was not retrieved. The report was rejected; retry generation.")
        claim.citation_ids = list(dict.fromkeys(claim.citation_ids))
        if not claim.citation_ids or any(sources[i].date_status != "in_window" for i in claim.citation_ids):
            claim.evidence = "uncertain"
    if any(c.evidence == "uncertain" for c in [*draft.summary, *draft.developments]):
        note = "Uncertain claims require verification. Citation presence is not independent fact-checking; review the source excerpts."
        if note not in draft.uncertainty:
            draft.uncertainty.append(note)
    text = " ".join([*(c.text for c in draft.summary), *(d.text + d.why_it_matters + d.discussion_point for d in draft.developments), *draft.questions, *draft.uncertainty])
    if len(text.split()) > 600 or any(len(q) > 220 for q in draft.questions) or any(len(n) > 260 for n in draft.uncertainty):
        raise BriefIQError("The model exceeded the one-page content budget. Retry generation.")
    return draft


def empty_draft():
    return Draft(summary=[Claim(text="Insufficient evidence to establish recent developments.")], developments=[],
                 questions=["What has changed most in your priorities over the past month?", "Which current initiatives should we understand before working together?", "What would make this meeting useful for you?"],
                 uncertainty=["No factual briefing can be established from the available evidence."])


def demo_draft(evidence):
    if not evidence.sources:
        return empty_draft()
    implications = [
        ("A limited pilot could offer a low-risk way to evaluate fit before a broader rollout.", "Which pilot outcomes and integration requirements should we agree on?"),
        ("An operations lead could become a useful owner for delivery coordination.", "Who should own timelines, escalation, and the next delivery checkpoint?"),
        ("A feedback program could create an opportunity to shape the partner experience.", "What feedback would be most useful before committing to a partnership?")]
    developments = [Development(text=s.excerpt, citation_ids=[s.id], evidence="source_backed",
                               why_it_matters=implications[i][0],
                               discussion_point=implications[i][1]) for i, s in enumerate(evidence.sources[:3])]
    return Draft(summary=[Claim(text="Fictional Northstar Labs is testing a product, growing its leadership team, and exploring a partnership.", citation_ids=[s.id for s in evidence.sources[:3]], evidence="source_backed")],
                 developments=developments, questions=["What would a successful pilot look like?", "Which decisions need alignment this month?", "How should we measure partnership readiness?"],
                 uncertainty=["DEMO: all organizations, events, and example.org references are fictional fixtures, not live research."])
