# Script to reorganize langgraph-app by moving non-core files to non-core-files directory
# Core files that should remain in root:
# - .git/ (version control)
# - .env, .env.example (environment)
# - .gitignore (git config)
# - LICENSE, README.md (documentation)
# - cli.py, cors_proxy.py, server_with_cors.py (server files)
# - langgraph.json, pyproject.toml (config)
# - src/ (source code)

Write-Host "Starting file reorganization..." -ForegroundColor Green

# Create non-core-files directory if it doesn't exist
if (!(Test-Path "non-core-files")) {
    New-Item -ItemType Directory -Path "non-core-files"
    Write-Host "Created non-core-files directory" -ForegroundColor Yellow
}

# List of files and folders to move (non-core items)
$itemsToMove = @(
    ".benchmarks",
    ".codespellignore", 
    ".coverage",
    ".langgraph_api",
    ".pytest_cache",
    "__pycache__",
    "agent.egg-info",
    "dev stuff",
    "scripts",
    "static",
    "supabase",
    "tests",
    "venv",
    "LANGSMITH_MVP.md",
    "MCP_IMPLEMENTATION_SUMMARY.md",
    "Makefile",
    "how langgraph",
    "run_experiment_on_dataset.py",
    "tatus",
    "test_graph.py",
    "test_mcp_cli.py",
    "test_schema.json",
    "verify_experiments.py"
)

$movedCount = 0
$skippedCount = 0

foreach ($item in $itemsToMove) {
    if (Test-Path $item) {
        try {
            Move-Item -Path $item -Destination "non-core-files/" -Force
            Write-Host "Moved: $item" -ForegroundColor Green
            $movedCount++
        }
        catch {
            Write-Host "Error moving $item : $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "Skipped: $item (not found)" -ForegroundColor Yellow
        $skippedCount++
    }
}

Write-Host "`nReorganization complete!" -ForegroundColor Green
Write-Host "Files/folders moved: $movedCount" -ForegroundColor Cyan
Write-Host "Items skipped: $skippedCount" -ForegroundColor Cyan

# Show final structure
Write-Host "`nCurrent root directory structure:" -ForegroundColor Magenta
Get-ChildItem -Path "." -Force | Where-Object { $_.Name -ne "non-core-files" } | ForEach-Object {
    $type = if ($_.PSIsContainer) { "DIR" } else { "FILE" }
    Write-Host "$type $($_.Name)" -ForegroundColor White
}

Write-Host "`nNon-core-files directory structure:" -ForegroundColor Magenta
if (Test-Path "non-core-files") {
    Get-ChildItem -Path "non-core-files" -Recurse | ForEach-Object {
        $indent = "  " * ($_.FullName.Split('\').Count - $PWD.Path.Split('\').Count - 2)
        $type = if ($_.PSIsContainer) { "DIR" } else { "FILE" }
        Write-Host "$indent$type $($_.Name)" -ForegroundColor Gray
    }
}
