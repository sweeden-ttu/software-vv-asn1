/**
 * BloomingDirectedGraph: each repository under ~/projects (except data-structures) is a node.
 * Edges are directed (e.g. flow to github_actions). Interacts with GitHub Actions API.
 * Usage: set GITHUB_TOKEN for API calls. Run with: npx ts-node blooming-graph.ts (or compile and node).
 */

import * as fs from "fs";
import * as path from "path";
import { execSync } from "child_process";

const PROJECTS_DIR = process.env.PROJECTS_DIR || path.join(process.env.HOME || "", "projects");
const EXCLUDE_REPOS = new Set(["data-structures"]);
const GITHUB_API = "https://api.github.com";

export interface Node {
  name: string;
  path: string;
  owner: string | null;
  repo: string | null;
  slug: string;
}

export interface Edge {
  from: string;
  to: string;
}

function gitRemoteOwnerRepo(repoPath: string): { owner: string | null; repo: string | null } {
  try {
    const out = execSync(`git -C ${JSON.stringify(repoPath)} remote get-url origin`, {
      encoding: "utf8",
      stdio: ["pipe", "pipe", "ignore"],
    }).trim();
    const m = out.match(/github\.com[:/]([^/]+)\/([^/\s]+?)(?:\.git)?$/);
    return m ? { owner: m[1], repo: m[2] } : { owner: null, repo: null };
  } catch {
    return { owner: null, repo: null };
  }
}

export class BloomingDirectedGraph {
  nodes: Node[] = [];
  edges: Edge[] = [];

  constructor(
    projectsDir: string = PROJECTS_DIR,
    exclude: Set<string> = EXCLUDE_REPOS
  ) {
    this.discoverNodes(projectsDir, exclude);
    this.discoverEdges();
  }

  private discoverNodes(projectsDir: string, exclude: Set<string>): void {
    if (!fs.existsSync(projectsDir) || !fs.statSync(projectsDir).isDirectory()) return;
    const entries = fs.readdirSync(projectsDir, { withFileTypes: true });
    const dirs = entries.filter((e) => e.isDirectory()).map((e) => e.name).sort();
    for (const name of dirs) {
      if (exclude.has(name)) continue;
      const repoPath = path.join(projectsDir, name);
      const gitDir = path.join(repoPath, ".git");
      if (!fs.existsSync(gitDir)) continue;
      const { owner, repo } = gitRemoteOwnerRepo(repoPath);
      this.nodes.push({
        name,
        path: repoPath,
        owner,
        repo,
        slug: repo || name,
      });
    }
  }

  private discoverEdges(): void {
    for (const n of this.nodes) {
      if (n.owner && n.repo) {
        this.edges.push({ from: n.name, to: "github_actions" });
      }
    }
  }

  nodeNames(): string[] {
    return this.nodes.map((n) => n.name);
  }

  private async request(
    method: string,
    apiPath: string,
    body?: object
  ): Promise<Record<string, unknown>> {
    const token = process.env.GITHUB_TOKEN;
    if (!token) return { error: "GITHUB_TOKEN not set" };
    const url = apiPath.startsWith("/") ? `${GITHUB_API}${apiPath}` : `${GITHUB_API}/${apiPath}`;
    const headers: Record<string, string> = {
      Accept: "application/vnd.github.v3+json",
      Authorization: `Bearer ${token}`,
    };
    const opts: RequestInit = { method, headers };
    if (body && ["POST", "PUT", "PATCH"].includes(method)) {
      opts.body = JSON.stringify(body);
      headers["Content-Type"] = "application/json";
    }
    try {
      const res = await fetch(url, opts);
      if (!res.ok) return { error: `HTTP ${res.status}` };
      const text = await res.text();
      return text ? (JSON.parse(text) as Record<string, unknown>) : {};
    } catch (e) {
      return { error: String(e) };
    }
  }

  async listWorkflows(owner: string, repo: string): Promise<Record<string, unknown>> {
    return this.request("GET", `/repos/${owner}/${repo}/actions/workflows`);
  }

  async listWorkflowRuns(
    owner: string,
    repo: string,
    workflowId?: number,
    perPage: number = 10
  ): Promise<Record<string, unknown>> {
    let apiPath = `/repos/${owner}/${repo}/actions/runs?per_page=${perPage}`;
    if (workflowId != null) apiPath += `&workflow_id=${workflowId}`;
    return this.request("GET", apiPath);
  }

  async triggerWorkflowDispatch(
    owner: string,
    repo: string,
    workflowId: string,
    ref: string = "main",
    inputs?: Record<string, string>
  ): Promise<Record<string, unknown>> {
    const body: Record<string, unknown> = { ref };
    if (inputs && Object.keys(inputs).length) body.inputs = inputs;
    const out = await this.request(
      "POST",
      `/repos/${owner}/${repo}/actions/workflows/${workflowId}/dispatches`,
      body
    );
    if ("error" in out) return out;
    return { ok: true };
  }

  async *eachRepoWorkflows(): AsyncGenerator<[string, string, string, Record<string, unknown>]> {
    for (const n of this.nodes) {
      if (!n.owner || !n.repo) continue;
      const list = await this.listWorkflows(n.owner, n.repo);
      yield [n.name, n.owner, n.repo, list];
    }
  }
}

async function main(): Promise<void> {
  const g = new BloomingDirectedGraph();
  console.log("Nodes:", g.nodeNames().join(", "));
  console.log("Edges:", g.edges.length, "(each node -> github_actions)");
  for await (const [name, owner, repo, list] of g.eachRepoWorkflows()) {
    if ("error" in list) {
      console.log(`${name}: ${list.error}`);
    } else {
      const workflows = (list.workflows as { name?: string }[]) || [];
      const names = workflows.map((w) => w.name || "?").join(", ");
      console.log(`${name} (${owner}/${repo}): ${workflows.length} workflow(s) - ${names}`);
    }
  }
}

if (require.main === module) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
