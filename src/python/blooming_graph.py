"""
BloomingDirectedGraph: each repository under ~/projects (except data-structures) is a node.
Edges are directed (e.g. flow to github_actions). Interacts with GitHub Actions API.
Usage: set GITHUB_TOKEN for API calls. See __main__ for CLI.
"""

import os
import re
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Tuple

PROJECTS_DIR = os.path.expanduser(os.environ.get("PROJECTS_DIR", "~/projects"))
EXCLUDE_REPOS = {"data-structures"}
GITHUB_API = "https://api.github.com"


def git_remote_owner_repo(path: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (owner, repo) from git remote get-url origin."""
    import subprocess
    try:
        out = subprocess.run(
            ["git", "-C", path, "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        url = (out.stdout or "").strip() if out.returncode == 0 else ""
    except Exception:
        return None, None
    if not url:
        return None, None
    # sweeden-ttu@github.com:sweeden-ttu/repo.git or https://github.com/sweeden-ttu/$repo_name
    match = re.search(r"github\.com[:/]([^/]+)/([^/\s]+?)(?:\.git)?$", url)
    return (match.group(1), match.group(2)) if match else (None, None)


class BloomingDirectedGraph:
    """Directed graph of repos as nodes; edges to github_actions."""

    def __init__(
        self,
        projects_dir: str = PROJECTS_DIR,
        exclude: Optional[set] = None,
    ):
        self.projects_dir = projects_dir
        self.exclude = exclude or EXCLUDE_REPOS
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, str]] = []
        self._discover_nodes()
        self._discover_edges()

    def _discover_nodes(self) -> None:
        if not os.path.isdir(self.projects_dir):
            return
        for name in sorted(os.listdir(self.projects_dir)):
            if name in self.exclude:
                continue
            path = os.path.join(self.projects_dir, name)
            if not os.path.isdir(path) or not os.path.isdir(os.path.join(path, ".git")):
                continue
            owner, repo = git_remote_owner_repo(path)
            self.nodes.append({
                "name": name,
                "path": path,
                "owner": owner,
                "repo": repo,
                "slug": repo or name,
            })
        return None

    def _discover_edges(self) -> None:
        for n in self.nodes:
            if n.get("owner") and n.get("repo"):
                self.edges.append({"from": n["name"], "to": "github_actions"})

    def node_names(self) -> List[str]:
        return [n["name"] for n in self.nodes]

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            return {"error": "GITHUB_TOKEN not set"}
        url = GITHUB_API + path if path.startswith("/") else f"{GITHUB_API}/{path}"
        req = urllib.request.Request(
            url,
            method=method,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"Bearer {token}",
            },
        )
        if data and method in ("POST", "PUT", "PATCH"):
            req.data = json.dumps(data).encode("utf-8")
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}"}
        except Exception as e:
            return {"error": str(e)}

    def list_workflows(self, owner: str, repo: str) -> Dict[str, Any]:
        return self._request("GET", f"/repos/{owner}/{repo}/actions/workflows")

    def list_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: Optional[int] = None,
        per_page: int = 10,
    ) -> Dict[str, Any]:
        path = f"/repos/{owner}/{repo}/actions/runs?per_page={per_page}"
        if workflow_id:
            path += f"&workflow_id={workflow_id}"
        return self._request("GET", path)

    def trigger_workflow_dispatch(
        self,
        owner: str,
        repo: str,
        workflow_id: str,
        ref: str = "main",
        inputs: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"ref": ref}
        if inputs:
            body["inputs"] = inputs
        resp = self._request(
            "POST",
            f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            data=body,
        )
        if "error" in resp:
            return resp
        return {"ok": True}

    def each_repo_workflows(self):
        """Yield (name, owner, repo, list_workflows_result) for each node with owner/repo."""
        for n in self.nodes:
            owner, repo = n.get("owner"), n.get("repo")
            if not owner or not repo:
                continue
            result = self.list_workflows(owner, repo)
            yield n["name"], owner, repo, result


def main() -> None:
    g = BloomingDirectedGraph()
    print("Nodes:", ", ".join(g.node_names()))
    print("Edges:", len(g.edges), "(each node -> github_actions)")
    for name, owner, repo, lst in g.each_repo_workflows():
        if "error" in lst:
            print(f"{name}: {lst['error']}")
        else:
            workflows = lst.get("workflows") or []
            names = ", ".join(w.get("name", "?") for w in workflows)
            print(f"{name} ({owner}/{repo}): {len(workflows)} workflow(s) - {names}")


if __name__ == "__main__":
    main()
