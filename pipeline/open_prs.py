"""Open or update one pull request per community skill. Used by the GitHub workflow.

    python -m pipeline.open_prs --report report.json --generated <folder> [--base main]

`--generated` is a copy of `shelf/community/` as the pipeline wrote it. For each skill
the run added, updated or removed, this script puts only that skill's folder on its own
branch (`community-skill/<slug>`), pushes it, and opens a pull request, or updates the
open one. It never merges and never pushes to the base branch.

It needs `git` and the GitHub command-line tool `gh`, signed in through GH_TOKEN.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SHELF = Path("shelf") / "community"
BRANCH_PREFIX = "community-skill/"
LABEL = "community-skill"

CHECKLIST = """\
### Review checklist (a person completes this before the merge)

- [ ] I read the whole skill file in this pull request.
- [ ] The skill is about Jewish text study or teaching, and I would be glad to see our name next to it.
- [ ] The skill does not tell the assistant to give a religious ruling or to invent a source.
- [ ] The author name and the licence in the file are correct.
- [ ] The safety report above shows "Passed" for the fixed rules, and I agree with the model review notes.
- [ ] I tried the skill once (see `docs/plugin/community-skills.md`, "Try a skill before you merge").

After the merge, the server deploys again and the skill appears on the live shelf for every user.
To take a skill down later, see "Remove a skill" in `docs/plugin/community-skills.md`.

_The community-skills workflow opened this pull request. The workflow cannot merge it._
"""

REMOVAL_CHECKLIST = """\
### Review checklist (a person completes this before the merge)

- [ ] I confirmed that the author unpublished the skill or withdrew consent in Yochai Create.

After the merge, the server deploys again and the skill leaves the live shelf.

_The community-skills workflow opened this pull request. The workflow cannot merge it._
"""


def sh(*args: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(args), check=check, text=True, capture_output=capture)


def remote_file(branch: str, path: Path) -> str | None:
    """The file's text on the remote branch, or None when the branch or file is absent."""
    done = sh("git", "show", f"origin/{branch}:{path.as_posix()}", check=False, capture=True)
    return done.stdout if done.returncode == 0 else None


def remote_branch_exists(branch: str) -> bool:
    return sh("git", "rev-parse", "--verify", "--quiet", f"origin/{branch}", check=False, capture=True).returncode == 0


def open_pr_number(branch: str) -> str | None:
    done = sh("gh", "pr", "list", "--head", branch, "--state", "open", "--json", "number", "--jq", ".[0].number", check=False, capture=True)
    number = done.stdout.strip()
    return number or None


def title_for(result: dict) -> str:
    name = result.get("title") or result["slug"]
    verb = {"added": "add", "updated": "update", "removed": "remove"}[result["status"]]
    return f'Community skill: {verb} "{name}"'[:120]


def body_for(result: dict) -> str:
    checklist = REMOVAL_CHECKLIST if result["status"] == "removed" else CHECKLIST
    return f"{result.get('report', '').rstrip()}\n\n{checklist}"


def process(result: dict, generated: Path, base: str) -> str:
    slug = result["slug"]
    branch = BRANCH_PREFIX + slug
    rel = SHELF / slug / "SKILL.md"
    source = generated / slug / "SKILL.md"
    wanted = source.read_text(encoding="utf-8") if source.is_file() else None
    if result["status"] != "removed" and wanted is None:
        return f"{slug}: no generated file, nothing to do"

    pr = open_pr_number(branch)
    if pr and remote_branch_exists(branch) and remote_file(branch, rel) == wanted:
        return f"{slug}: pull request #{pr} is already up to date"

    sh("git", "checkout", "--quiet", "-B", branch, f"origin/{base}")
    target = Path(rel)
    if wanted is None:
        if target.exists():
            sh("git", "rm", "--quiet", "-r", "--", (SHELF / slug).as_posix())
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(wanted, encoding="utf-8")
        sh("git", "add", "--", rel.as_posix())
    if sh("git", "diff", "--cached", "--quiet", check=False).returncode == 0:
        return f"{slug}: the base branch already matches, no pull request needed"

    verb = {"added": "add", "updated": "update", "removed": "remove"}[result["status"]]
    sh("git", "commit", "--quiet", "-m", f"community skill: {verb} {slug}",
       "-m", f"Source: Yochai Create method {result.get('method_id', '')}")
    sh("git", "push", "--quiet", "--force", "origin", f"HEAD:refs/heads/{branch}")

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
        handle.write(body_for(result))
        body_file = handle.name
    if pr:
        sh("gh", "pr", "edit", pr, "--title", title_for(result), "--body-file", body_file)
        return f"{slug}: updated pull request #{pr}"
    created = sh("gh", "pr", "create", "--base", base, "--head", branch, "--title", title_for(result),
                 "--body-file", body_file, check=False, capture=True)
    if created.returncode != 0:
        return f"{slug}: could not open a pull request: {created.stderr.strip()[:300]}"
    sh("gh", "pr", "edit", created.stdout.strip().rsplit("/", 1)[-1], "--add-label", LABEL, check=False, capture=True)
    return f"{slug}: opened {created.stdout.strip()}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--report", required=True)
    parser.add_argument("--generated", required=True)
    parser.add_argument("--base", default="main")
    args = parser.parse_args(argv)

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    generated = Path(args.generated)
    todo = [r for r in report["results"] if r["status"] in {"added", "updated", "removed"}]
    if not todo:
        print("No skill changed. No pull request to open.")
        return 0

    # Start from a clean tree: the pipeline's own output must not leak into every branch.
    sh("git", "checkout", "--quiet", "--", ".")
    if SHELF.exists():
        sh("git", "clean", "--quiet", "-fd", "--", SHELF.as_posix())
    sh("git", "fetch", "--quiet", "origin", "+refs/heads/*:refs/remotes/origin/*")

    failed = False
    for result in todo:
        try:
            message = process(result, generated, args.base)
        except subprocess.CalledProcessError as exc:
            message = f"{result['slug']}: a git or gh command failed ({exc.cmd[0]} {exc.cmd[1] if len(exc.cmd) > 1 else ''})"
            failed = True
        failed = failed or "could not open" in message
        print(message)
    sh("git", "checkout", "--quiet", "--detach", f"origin/{args.base}", check=False)
    return 1 if failed else 0


if __name__ == "__main__":
    shutil.which("gh") or sys.exit("The GitHub command-line tool `gh` is not installed.")
    raise SystemExit(main())
