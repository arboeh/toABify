"""Guards the YAML examples in the README files.

Every example must stay valid against the current notify service schema, so a
documentation change cannot silently advertise a call that Home Assistant
rejects at runtime (as happened with the removed string form of `onClick`).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from custom_components.toabify.notify import _NOTIFY_DATA_SCHEMA

REPO_ROOT = Path(__file__).resolve().parent.parent
README_FILES = (REPO_ROOT / "README.md", REPO_ROOT / "README.de.md")

# Keys the core notify schema accepts on the payload level. Every toast option
# belongs in the nested "data" key.
_CORE_PAYLOAD_KEYS = frozenset({"message", "title", "target", "data"})

_YAML_BLOCK_RE = re.compile(r"```yaml\s*\n(?P<body>.*?)```", re.DOTALL)


def _yaml_blocks(path: Path) -> list[object]:
    """Return the parsed content of every ```yaml block in *path*."""
    text = path.read_text(encoding="utf-8")
    return [yaml.safe_load(match.group("body")) for match in _YAML_BLOCK_RE.finditer(text)]


def _toast_examples(path: Path) -> list[tuple[int, dict]]:
    """Return ``(block index, config)`` for every block calling notify.toabify.

    Both the current ``action:`` form and the legacy ``service:`` form are
    collected, because both are valid Home Assistant call syntax.
    """
    examples: list[tuple[int, dict]] = []
    for index, block in enumerate(_yaml_blocks(path)):
        if not isinstance(block, dict):
            continue
        service = block.get("action") or block.get("service")
        if service == "notify.toabify":
            examples.append((index, block))
    return examples


def _example_problems(readme: str, block_index: int, example: dict) -> list[str]:
    """Return a human readable problem for every deviation in *example*."""
    problems: list[str] = []
    payload = example.get("data")
    if not isinstance(payload, dict):
        return [f"{readme} yaml block {block_index}: 'data' must be a mapping"]

    message = payload.get("message")
    if not isinstance(message, str) or not message.strip():
        problems.append(f"{readme} yaml block {block_index}: 'message' must be a non-empty string")

    stray = sorted(set(payload) - _CORE_PAYLOAD_KEYS)
    if stray:
        problems.append(
            f"{readme} yaml block {block_index}: {stray} belong in the nested 'data' key"
        )

    options = payload.get("data")
    if isinstance(options, dict):
        try:
            _NOTIFY_DATA_SCHEMA({k: v for k, v in options.items() if v is not None})
        except Exception as err:
            problems.append(f"{readme} yaml block {block_index}: {err}")
    return problems


def _example_ids() -> list[pytest.ParameterSet]:
    ids: list[pytest.ParameterSet] = []
    for path in README_FILES:
        for index, config in _toast_examples(path):
            message = config["data"]["message"]
            ids.append(
                pytest.param(path.name, index, config, id=f"{path.name}-block{index}-{message}")
            )
    return ids


@pytest.mark.parametrize(("readme", "block_index", "example"), _example_ids())
def test_readme_example_is_valid(readme: str, block_index: int, example: dict) -> None:
    """Each README example must survive the notify data schema."""
    assert not _example_problems(readme, block_index, example)


@pytest.mark.parametrize("readme", README_FILES, ids=lambda path: path.name)
def test_readme_contains_a_toast_example(readme: Path) -> None:
    """Both README files must keep documenting the notify service."""
    assert _toast_examples(readme)


_BROKEN_EXAMPLES: dict[str, str] = {
    "action form with string onClick": (
        'action: notify.toabify\ndata:\n  message: "broken"\n  data:\n    onClick: "/lovelace/0"\n'
    ),
    "service form with string onClick": (
        'service: notify.toabify\ndata:\n  message: "broken"\n  data:\n    onClick: "/lovelace/0"\n'
    ),
    "option on payload level": (
        'action: notify.toabify\ndata:\n  message: "broken"\n  onClick: "/lovelace/0"\n'
    ),
    "invalid color": (
        'action: notify.toabify\ndata:\n  message: "broken"\n  data:\n    color: purple\n'
    ),
    "unknown key in data": (
        'action: notify.toabify\ndata:\n  message: "broken"\n  data:\n    nope: 1\n'
    ),
    "gravity: middle": (
        'action: notify.toabify\ndata:\n  message: "broken"\n  data:\n    gravity: middle\n'
    ),
    "duration above the maximum": (
        'action: notify.toabify\ndata:\n  message: "broken"\n  data:\n    duration: 700000\n'
    ),
    "empty message": 'action: notify.toabify\ndata:\n  message: ""\n',
}


@pytest.mark.parametrize("body", _BROKEN_EXAMPLES.values(), ids=list(_BROKEN_EXAMPLES))
def test_guard_catches_broken_examples(body: str) -> None:
    """The guard must fail on every shape of a broken example."""
    example = yaml.safe_load(body)
    problems = _example_problems("synthetic.md", 0, example)
    assert problems, "a broken example slipped through the guard"


def test_guard_accepts_a_valid_example() -> None:
    """A correct example must produce no problems."""
    example = {
        "action": "notify.toabify",
        "data": {"message": "fine", "data": {"color": "success", "visibility": "all"}},
    }
    assert not _example_problems("synthetic.md", 0, example)
