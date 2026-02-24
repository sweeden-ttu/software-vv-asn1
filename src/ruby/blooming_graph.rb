# frozen_string_literal: true

# BloomingDirectedGraph: each repository under ~/projects (except data-structures) is a node.
# Edges are directed (e.g. flow by context key: owner -> hpcc -> github). Interacts with GitHub Actions API.
# Usage: see run script at bottom; set GITHUB_TOKEN for API calls.

require "json"
require "net/http"
require "uri"
require "shellwords"

PROJECTS_DIR = ENV.fetch("PROJECTS_DIR", File.expand_path("~/projects"))
EXCLUDE_REPOS = %w[data-structures].freeze
GITHUB_API = "https://api.github.com"

# Node: one repo (name, path, owner, repo from git remote).
# Edge: from_node -> to_node (string names).
class BloomingDirectedGraph
  attr_reader :nodes, :edges

  def initialize(projects_dir: PROJECTS_DIR, exclude: EXCLUDE_REPOS)
    @projects_dir = projects_dir
    @exclude = exclude
    @nodes = []   # [{ name:, path:, owner:, repo:, slug: }]
    @edges = []  # [{ from:, to: }]
    discover_nodes
    discover_edges
  end

  def discover_nodes
    return unless Dir.exist?(@projects_dir)

    Dir.children(@projects_dir).sort.each do |name|
      next if @exclude.include?(name)
      path = File.join(@projects_dir, name)
      next unless File.directory?(path) && File.directory?(File.join(path, ".git"))

      owner, repo = git_remote_owner_repo(path)
      @nodes << {
        name: name,
        path: path,
        owner: owner,
        repo: repo,
        slug: repo || name
      }
    end
  end

  def git_remote_owner_repo(path)
    url = `git -C #{Shellwords.shellescape(path)} remote get-url origin 2>/dev/null`.strip
    return [nil, nil] if url.empty?

    # git@github.com:owner/repo.git or https://github.com/owner/repo
    m = url.match(%r{github\.com[:/]([^/]+)/([^/\s]+?)(?:\.git)?$})
    m ? [m[1], m[2]] : [nil, nil]
  end

  # Directed edges: by default link repo nodes to "github_actions" when they have workflows.
  def discover_edges
    @nodes.each do |n|
      @edges << { from: n[:name], to: "github_actions" } if n[:owner] && n[:repo]
    end
  end

  def node_names
    @nodes.map { |n| n[:name] }
  end

  # --- GitHub Actions API (requires GITHUB_TOKEN) ---

  def list_workflows(owner:, repo:)
    token = ENV["GITHUB_TOKEN"]
    return { error: "GITHUB_TOKEN not set" } unless token

    uri = URI("#{GITHUB_API}/repos/#{owner}/#{repo}/actions/workflows")
    req = Net::HTTP::Get.new(uri)
    req["Accept"] = "application/vnd.github.v3+json"
    req["Authorization"] = "Bearer #{token}"

    res = Net::HTTP.start(uri.hostname, uri.port, use_ssl: uri.scheme == "https") { |http| http.request(req) }
    return { error: "HTTP #{res.code}" } unless res.is_a?(Net::HTTPSuccess)

    JSON.parse(res.body)
  end

  def list_workflow_runs(owner:, repo:, workflow_id: nil, per_page: 10)
    token = ENV["GITHUB_TOKEN"]
    return { error: "GITHUB_TOKEN not set" } unless token

    path = "/repos/#{owner}/#{repo}/actions/runs?per_page=#{per_page}"
    path += "&workflow_id=#{workflow_id}" if workflow_id
    uri = URI("#{GITHUB_API}#{path}")
    req = Net::HTTP::Get.new(uri)
    req["Accept"] = "application/vnd.github.v3+json"
    req["Authorization"] = "Bearer #{token}"

    res = Net::HTTP.start(uri.hostname, uri.port, use_ssl: uri.scheme == "https") { |http| http.request(req) }
    return { error: "HTTP #{res.code}" } unless res.is_a?(Net::HTTPSuccess)

    JSON.parse(res.body)
  end

  def trigger_workflow_dispatch(owner:, repo:, workflow_id:, ref: "main", inputs: {})
    token = ENV["GITHUB_TOKEN"]
    return { error: "GITHUB_TOKEN not set" } unless token

    uri = URI("#{GITHUB_API}/repos/#{owner}/#{repo}/actions/workflows/#{workflow_id}/dispatches")
    req = Net::HTTP::Post.new(uri)
    req["Accept"] = "application/vnd.github.v3+json"
    req["Authorization"] = "Bearer #{token}"
    req["Content-Type"] = "application/json"
    body = { ref: ref }.merge(inputs.empty? ? {} : { inputs: inputs })
    req.body = body.to_json

    res = Net::HTTP.start(uri.hostname, uri.port, use_ssl: uri.scheme == "https") { |http| http.request(req) }
    return { error: "HTTP #{res.code}" } unless res.is_a?(Net::HTTPSuccess)

    { ok: true }
  end

  # Interact with GitHub Actions for each node (repo) that has owner/repo.
  def each_repo_workflows(&block)
    @nodes.each do |n|
      next unless n[:owner] && n[:repo]
      list = list_workflows(owner: n[:owner], repo: n[:repo])
      block.call(n[:name], n[:owner], n[:repo], list)
    end
  end
end

# CLI
if __FILE__ == $PROGRAM_NAME
  g = BloomingDirectedGraph.new
  puts "Nodes: #{g.node_names.join(', ')}"
  puts "Edges: #{g.edges.size} (each node -> github_actions)"
  g.each_repo_workflows do |name, owner, repo, list|
    if list.key?(:error)
      puts "#{name}: #{list[:error]}"
    else
      workflows = list.dig("workflows") || []
      puts "#{name} (#{owner}/#{repo}): #{workflows.size} workflow(s) - #{workflows.map { |w| w['name'] }.join(', ')}"
    end
  end
end
