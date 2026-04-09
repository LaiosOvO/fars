from pathlib import Path
import subprocess

from fars_kg.worktree import GitWorktreeManager


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    (path / "README.md").write_text("# temp repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True, text=True)


def test_git_worktree_manager_creates_worktree(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)
    worktree_root = tmp_path / "worktrees"

    manager = GitWorktreeManager(str(repo_root), str(worktree_root))
    allocation = manager.create_worktree(run_id=7, branch_name="exp-branch-7")

    assert allocation.run_id == 7
    assert allocation.branch_name == "exp-branch-7"
    assert Path(allocation.worktree_path).exists()
    assert (Path(allocation.worktree_path) / ".git").exists()

