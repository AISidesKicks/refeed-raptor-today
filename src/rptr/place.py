"""Load and validate a demo place.

A place is data, not code. The loader reads `demo.toml`, the corpus manifest,
the Markdown documents, the script, and the eval file. It fails closed when a
gold document is missing or a document is malformed.
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class PlaceError(ValueError):
    """Raised when a place folder does not follow the contract."""


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    category: str
    date: str
    author: str
    source: str
    path: str
    text: str
    words: int


@dataclass(frozen=True)
class Question:
    id: str
    question: str
    type: str
    gold: tuple[str, ...]
    expected: str
    notes: str = ""


@dataclass(frozen=True)
class ScriptTurn:
    turn: int
    visitor: str
    note: str = ""
    expect: str = ""


@dataclass(frozen=True)
class Place:
    id: str
    title: str
    blurb: str
    root: Path
    corpus_dir: Path
    script_path: Path
    eval_path: Path
    license: str
    version: int
    starter_questions: tuple[str, ...]
    models: dict[str, str]
    documents: tuple[Document, ...]
    questions: tuple[Question, ...]
    script: tuple[ScriptTurn, ...]
    manifest: dict[str, Any] = field(repr=False)

    @property
    def words(self) -> int:
        return sum(doc.words for doc in self.documents)

    @property
    def doc_ids(self) -> set[str]:
        return {doc.id for doc in self.documents}

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "blurb": self.blurb,
            "license": self.license,
            "version": self.version,
            "documents": len(self.documents),
            "words": self.words,
            "questions": len(self.questions),
            "starter_questions": list(self.starter_questions),
            "models": self.models,
        }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise PlaceError(f"missing file: {path}")
    records: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PlaceError(f"{path}:{number}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise PlaceError(f"{path}:{number}: expected a JSON object")
        records.append(value)
    return records


def _parse_document(path: Path, rel_path: str, doc_id: str) -> Document:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("# "):
        raise PlaceError(f"{path}: first line must be a level-one heading")
    title = lines[0][2:].strip()
    meta: dict[str, str] = {}
    index = 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    while index < len(lines) and lines[index].strip():
        line = lines[index]
        if ":" not in line:
            raise PlaceError(f"{path}:{index + 1}: expected 'Key: value'")
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip()
        index += 1
    body = "\n".join(lines[index:]).strip()
    if not body:
        raise PlaceError(f"{path}: empty body")
    missing = [key for key in ("category", "date", "author", "source") if not meta.get(key)]
    if missing:
        raise PlaceError(f"{path}: missing metadata {missing}")
    return Document(
        id=doc_id,
        title=title,
        category=meta["category"],
        date=meta["date"],
        author=meta["author"],
        source=meta["source"],
        path=rel_path,
        text=body,
        words=len(body.split()),
    )


def load_place(path: Path) -> Place:
    root = Path(path).resolve()
    demo_path = root / "demo.toml"
    if not demo_path.is_file():
        raise PlaceError(f"{root}: missing demo.toml")
    try:
        meta = tomllib.loads(demo_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise PlaceError(f"{demo_path}: invalid TOML: {exc}") from exc

    required = (
        "id",
        "title",
        "blurb",
        "corpus",
        "script",
        "eval",
        "license",
        "version",
        "starter_questions",
    )
    missing = [key for key in required if key not in meta]
    if missing:
        raise PlaceError(f"{demo_path}: missing fields {missing}")

    place_id = str(meta["id"])
    if place_id != root.name:
        raise PlaceError(f"{root}: place id '{place_id}' does not match the folder name")

    starter = meta["starter_questions"]
    if not isinstance(starter, list) or not starter:
        raise PlaceError(f"{demo_path}: starter_questions must be a non-empty list")

    corpus_dir = (root / str(meta["corpus"])).resolve()
    manifest_path = corpus_dir / "manifest.json"
    if not manifest_path.is_file():
        raise PlaceError(f"{corpus_dir}: missing manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PlaceError(f"{manifest_path}: invalid JSON: {exc}") from exc
    entries = manifest.get("documents")
    if not isinstance(entries, list) or not entries:
        raise PlaceError(f"{manifest_path}: documents must be a non-empty list")

    documents: list[Document] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise PlaceError(f"{manifest_path}: every document entry must be an object")
        doc_id = str(entry.get("id", "")).strip()
        rel_path = str(entry.get("path", "")).strip()
        if not doc_id or not rel_path:
            raise PlaceError(f"{manifest_path}: every document needs id and path")
        if doc_id in seen:
            raise PlaceError(f"{manifest_path}: duplicate document id {doc_id}")
        seen.add(doc_id)
        doc_path = (root / rel_path).resolve()
        if not doc_path.is_file():
            raise PlaceError(f"{doc_path}: listed in the manifest but missing")
        document = _parse_document(doc_path, rel_path, doc_id)
        manifest_title = str(entry.get("title", "")).strip()
        if manifest_title and manifest_title != document.title:
            raise PlaceError(f"{doc_path}: title does not match the manifest")
        documents.append(document)

    script_path = (root / str(meta["script"])).resolve()
    script: list[ScriptTurn] = []
    for record in _read_jsonl(script_path):
        turn = int(record.get("turn", 0))
        visitor = str(record.get("visitor", "")).strip()
        if turn <= 0 or not visitor:
            raise PlaceError(f"{script_path}: every turn needs a positive turn and a visitor")
        script.append(
            ScriptTurn(
                turn=turn,
                visitor=visitor,
                note=str(record.get("note", "")),
                expect=str(record.get("expect", "")),
            )
        )
    script.sort(key=lambda item: item.turn)

    eval_path = (root / str(meta["eval"])).resolve()
    questions: list[Question] = []
    question_ids: set[str] = set()
    for record in _read_jsonl(eval_path):
        question_id = str(record.get("id", "")).strip()
        question = str(record.get("question", "")).strip()
        question_type = str(record.get("type", "single")).strip()
        expected = str(record.get("expected", "")).strip()
        gold = record.get("gold")
        if not question_id or not question or not expected:
            raise PlaceError(f"{eval_path}: every question needs id, question, and expected")
        if question_id in question_ids:
            raise PlaceError(f"{eval_path}: duplicate question id {question_id}")
        question_ids.add(question_id)
        if question_type not in {"single", "multi"}:
            raise PlaceError(f"{eval_path}: {question_id} has type {question_type}")
        if not isinstance(gold, list) or not gold:
            raise PlaceError(f"{eval_path}: {question_id} needs a non-empty gold list")
        gold_ids = tuple(str(item) for item in gold)
        missing_gold = [item for item in gold_ids if item not in seen]
        if missing_gold:
            raise PlaceError(f"{eval_path}: {question_id} has unknown gold docs {missing_gold}")
        questions.append(
            Question(
                id=question_id,
                question=question,
                type=question_type,
                gold=gold_ids,
                expected=expected,
                notes=str(record.get("notes", "")),
            )
        )

    models = meta.get("models", {})
    if not isinstance(models, dict):
        raise PlaceError(f"{demo_path}: [models] must be a table")

    return Place(
        id=place_id,
        title=str(meta["title"]),
        blurb=str(meta["blurb"]),
        root=root,
        corpus_dir=corpus_dir,
        script_path=script_path,
        eval_path=eval_path,
        license=str(meta["license"]),
        version=int(meta["version"]),
        starter_questions=tuple(str(item) for item in starter),
        models={str(key): str(value) for key, value in models.items()},
        documents=tuple(documents),
        questions=tuple(questions),
        script=tuple(script),
        manifest=manifest,
    )


def discover_places(root: Path) -> list[Place]:
    root = Path(root).resolve()
    if not root.is_dir():
        return []
    places: list[Place] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "demo.toml").is_file():
            places.append(load_place(child))
    return places
