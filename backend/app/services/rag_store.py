from __future__ import annotations
import csv, re
from dataclasses import dataclass
from pathlib import Path

TOKEN_RE = re.compile(r"[a-zA-ZÀ-ÿ0-9]+")

@dataclass
class DocumentChunk:
    source: str
    content: str
    metadata: dict

class ClinicRAGStore:
    def __init__(self, knowledge_dir: Path):
        self.knowledge_dir = knowledge_dir
        self.chunks: list[DocumentChunk] = []
        self.treatments: list[dict[str, str]] = []
        self.load()

    def load(self):
        self.chunks.clear()
        for path in sorted(self.knowledge_dir.glob('*.md')):
            text = path.read_text(encoding='utf-8')
            for i, chunk in enumerate(re.split(r"\n(?=# )", text)):
                if chunk.strip():
                    self.chunks.append(DocumentChunk(path.name, chunk.strip(), {'chunk': i, 'type': 'policy'}))
        tfile = self.knowledge_dir / 'treatment_durations.csv'
        if tfile.exists():
            with tfile.open(newline='', encoding='utf-8') as f:
                self.treatments = list(csv.DictReader(f))
            for row in self.treatments:
                self.chunks.append(DocumentChunk('treatment_durations.csv', '; '.join(f'{k}: {v}' for k,v in row.items()), {'type':'treatment'}))
        dfile = self.knowledge_dir / 'doctors.csv'
        if dfile.exists():
            with dfile.open(newline='', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    self.chunks.append(DocumentChunk('doctors.csv', '; '.join(f'{k}: {v}' for k,v in row.items()), {'type':'doctor'}))

    def query(self, question: str, k: int = 4) -> list[dict]:
        q = set(self.tokens(question))
        scored = []
        for chunk in self.chunks:
            score = len(q & set(self.tokens(chunk.content)))
            if score:
                scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{'source': c.source, 'content': c.content, 'metadata': c.metadata, 'score': s} for s,c in scored[:k]]

    def infer_treatment(self, reason: str | None) -> dict:
        reason = (reason or '').lower()
        synonyms = {
            'pain': 'Tooth pain consultation', 'toothache': 'Tooth pain consultation', 'clean': 'Dental cleaning',
            'whitening': 'Teeth whitening', 'white': 'Teeth whitening', 'extract': 'Tooth extraction',
            'implant': 'Implant consultation', 'braces': 'Braces consultation', 'swelling': 'Emergency swelling',
            'emergency': 'Emergency swelling'
        }
        target = next((v for k,v in synonyms.items() if k in reason), None)
        row = None
        if target:
            row = next((r for r in self.treatments if r.get('treatment','').lower() == target.lower()), None)
        row = row or (self.treatments[0] if self.treatments else {})
        return {
            'treatment': row.get('treatment', 'Dental consultation'),
            'duration_minutes': int(row.get('duration_minutes', '30')),
            'requires_doctor_approval': row.get('requires_doctor_approval', 'true').lower() == 'true',
            'urgency_level': row.get('urgency_level', 'normal')
        }

    @staticmethod
    def tokens(text: str) -> list[str]:
        return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]
