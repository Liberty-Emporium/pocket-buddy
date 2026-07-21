"""
AI organizer. Classifies and summarizes unprocessed documents.

JAY LAW: this only ever reads the real uploaded file. It never invents a
document, a client, or a fact. If the file can't be read or the API is
unavailable, the document is simply left unprocessed and reported — nothing
is fabricated.

Usage:
    python manage.py organize_daily              # all organizations
    python manage.py organize_daily --org goins-law
    python manage.py organize_daily --limit 20
"""

import json

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Organization
from documents.models import Document

VALID_CATEGORIES = {c.value for c in Document.Category if c.value != "unsorted"}

PROMPT = (
    "You are a legal filing assistant. Look at the document below and classify "
    "it into exactly ONE of these categories: contract, motion, evidence, "
    "correspondence, financial, other. Then write a 1-2 sentence plain-English "
    "summary of what it is, based ONLY on the text provided. Do not invent "
    "facts. If you cannot tell, use category 'other' and say so.\n\n"
    'Respond with ONLY JSON: {{"category": "...", "summary": "..."}}\n\n'
    "FILE NAME: {name}\n\nDOCUMENT TEXT (may be empty or partial):\n{text}\n"
)


def extract_text(doc, max_chars=6000):
    """Pull readable text from a document. Returns '' if not extractable."""
    ext = doc.extension
    try:
        if ext == "pdf":
            from pypdf import PdfReader

            doc.file.open("rb")
            reader = PdfReader(doc.file)
            parts = []
            for page in reader.pages[:15]:
                parts.append(page.extract_text() or "")
                if sum(len(p) for p in parts) > max_chars:
                    break
            return "\n".join(parts)[:max_chars]
        if ext in ("txt", "csv", "rtf", "eml"):
            doc.file.open("rb")
            return doc.file.read(max_chars).decode("utf-8", errors="replace")
    except Exception:
        return ""
    finally:
        try:
            doc.file.close()
        except Exception:
            pass
    return ""


def classify(name, text):
    """Call the AI. Returns (category, summary) or raises."""
    body = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "user", "content": PROMPT.format(name=name, text=text or "(no extractable text)")}
        ],
        "temperature": 0.1,
    }
    resp = requests.post(
        f"{settings.AI_API_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=60,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()
    # Model may wrap JSON in ```json fences.
    if content.startswith("```"):
        content = content.strip("`").split("\n", 1)[-1]
        if content.endswith("```"):
            content = content[:-3]
    data = json.loads(content)
    category = str(data.get("category", "other")).lower().strip()
    if category not in VALID_CATEGORIES:
        category = "other"
    summary = str(data.get("summary", "")).strip()[:2000]
    return category, summary


class Command(BaseCommand):
    help = "Classify and summarize unprocessed documents with the AI organizer."

    def add_arguments(self, parser):
        parser.add_argument("--org", help="Organization slug (default: all).")
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        if not settings.AI_API_KEY:
            self.stdout.write(
                self.style.WARNING(
                    "AI_API_KEY not set — skipping AI processing. "
                    "Documents left unsorted (nothing invented)."
                )
            )
            return

        qs = Document.objects.filter(ai_processed_at__isnull=True)
        if options.get("org"):
            org = Organization.objects.filter(slug=options["org"]).first()
            if not org:
                self.stderr.write(f"No organization with slug '{options['org']}'.")
                return
            qs = qs.filter(organization=org)
        qs = qs.order_by("created_at")[: options["limit"]]

        total = qs.count()
        self.stdout.write(f"Processing {total} document(s)…")
        done = failed = 0

        for doc in qs:
            name = doc.original_name or doc.title or f"doc-{doc.pk}"
            text = extract_text(doc)
            try:
                category, summary = classify(name, text)
                doc.category = category
                doc.ai_summary = summary
                doc.ai_processed_at = timezone.now()
                doc.save(update_fields=["category", "ai_summary", "ai_processed_at"])
                done += 1
                self.stdout.write(f"  ✓ #{doc.pk} {name} → {category}")
            except Exception as e:
                failed += 1
                self.stderr.write(f"  ✗ #{doc.pk} {name}: {e}")

        self.stdout.write(
            self.style.SUCCESS(f"Done. {done} processed, {failed} failed.")
        )
