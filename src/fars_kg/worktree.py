from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass
class WorktreeAllocation:
    run_id: int
    branch_name: str
    worktree_path: str
    repo_root: str


class GitWorktreeManager:
    def __init__(self, repo_root: str, worktree_root: str) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.worktree_root = Path(worktree_root).resolve()

    def create_worktree(self, run_id: int, branch_name: str) -> WorktreeAllocation:
        self._ensure_repo_ready()
        self.worktree_root.mkdir(parents=True, exist_ok=True)
        branch = branch_name or f"run-{run_id}"
        target_path = self.worktree_root / branch
        if not target_path.exists():
            self._run_git("worktree", "add", "-b", branch, str(target_path))
        return WorktreeAllocation(
            run_id=run_id,
            branch_name=branch,
            worktree_path=str(target_path),
            repo_root=str(self.repo_root),
        )

    def _ensure_repo_ready(self) -> None:
        inside = self._run_git("rev-parse", "--is-inside-work-tree", capture_output=True).strip()
        if inside != "true":
            raise ValueError(f"Repository root is not a git work tree: {self.repo_root}")
        try:
            self._run_git("rev-parse", "--verify", "HEAD", capture_output=True)
        except RuntimeError as exc:
            raise ValueError("Repository has no commits; git worktree requires an initial commit") from exc

    def _run_git(self, *args: str, capture_output: bool = False) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_root,
            check=False,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(stderr or f"git {' '.join(args)} failed")
        if capture_output:
            return result.stdout.strip()
        return result.stdout.strip()
