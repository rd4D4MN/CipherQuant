#!/usr/bin/env bash

# -------------------------------------------------------------------------
# This script creates multiple GitHub issues with proper multiline bodies,
# by storing each issue's body as a single-line string containing \n,
# and then interpreting those \n's with echo -e.
#
# 1) Install GitHub CLI: https://cli.github.com/manual/installation
# 2) Run `gh auth login`
# 3) Adjust REPO_OWNER, REPO_NAME, and ISSUES array below
# 4) `chmod +x scripts/create_issues.sh && ./scripts/create_issues.sh`
# -------------------------------------------------------------------------

REPO_OWNER="rd4D4MN"
REPO_NAME="CipherQuant"

# Each array element is "TITLE###BODY"
# For multi-line BODY, we embed \n for newlines and rely on echo -e to interpret them.

ISSUES=(
  "feat: Introduce Go-based Scraper and CLI Tool###**Description**:\n1. Create a new folder (\`go_scrapers/\`) with a Go-based scraper (e.g., [Colly](https://github.com/gocolly/colly)).\n2. Build a simple CLI command (e.g., \`./cipherquant compare --base=BTC --quote=ETH --days=30\`).\n3. Document Go usage in the README."
  "feat: Add Database Schema & Query Examples###**Description**:\n1. Create a \`db/\` folder with \`schema.sql\` (tables for prices, volumes, vc_investors).\n2. Add sample queries to a \`queries/\` folder (e.g., \`top_investors.sql\`, \`correlation_analysis.sql\`).\n3. Demonstrate one query in code or docs."
  "docs: Overhaul README with Architecture Diagram & Fintech Context###**Description**:\n1. Add a MermaidJS or similar diagram illustrating data flow.\n2. Include a 'Why This Matters for Fintech' section.\n3. Embed a short GIF or Loom video of the dashboard."
  "enhancement: Multi-Source Scraping with Anti-Bot Measures###**Description**:\n1. Scrape multiple sources: CoinGecko (Python), Yahoo Finance (Go), Crunchbase (Python).\n2. Add rotating proxies/user agents (e.g., [fake-useragent](https://pypi.org/project/fake-useragent/)).\n3. Document anti-bot tactics in \`scraping.md\`."
  "feat: REST API with Go (Gin) + Data Pipeline Tests###**Description**:\n1. Implement a Go REST API using [Gin](https://github.com/gin-gonic/gin) (e.g., \`/analysis/risk/:coin\`).\n2. Add tests (pytest/Go) for data validation and API consistency.\n3. Document endpoints in README or \`api.md\`."
  "feat(frontend): Production-Ready React Dashboard###**Description**:\n1. Finalize/improve the React build (Create React App or Vite).\n2. Add interactive charts ([D3.js](https://d3js.org/) or [Recharts](https://recharts.org/)) for correlation analysis.\n3. Provide a Dockerfile and environment config instructions."
  "enhancement: Expand AI/ML Models and Add Financial Evaluation###**Description**:\n1. Compare an LSTM with simpler models (ARIMA, Prophet) in a notebook.\n2. Add financial metrics like Sharpe ratio, ROI calculations.\n3. Integrate SHAP for model interpretability."
  "feat: Add VC/Private Equity Analysis Components###**Description**:\n1. Use Crunchbase or a similar data source to identify leading crypto VCs.\n2. Create scripts correlating VC investments to token performance (IRR vs. returns).\n3. Document relevance for fintech/PE roles in the README."
  "chore: Adopt Conventional Commits and Improve Branch Workflow###**Description**:\n1. Enforce [Conventional Commits](https://www.conventionalcommits.org/) with a linter.\n2. Optionally rewrite older commits via interactive rebase.\n3. Document your branching strategy (feature branches, PR merges, etc.)."
  "chore: Add GitHub Actions for CI/CD + Deployment###**Description**:\n1. Set up GitHub Actions for Go/Python linting and automated tests.\n2. Optionally deploy to Fly.io or another free-tier platform.\n3. Add a status badge to the README for the build process."
)

# Create issues from the array
for entry in "${ISSUES[@]}"; do

  # Split into title and body on '###'
  IFS="###" read -r TITLE RAW_BODY <<< "$entry"

  echo "Creating issue: $TITLE"

  # 1) Interpret \n in RAW_BODY as actual newlines using echo -e
  # 2) Write it out to a temporary file
  echo -e "$RAW_BODY" > bodytemp.md

  # Use the file as the body
  gh issue create \
    --repo "${REPO_OWNER}/${REPO_NAME}" \
    --title "$TITLE" \
    --body-file bodytemp.md

  echo "Issue created: $TITLE"
  echo "--------------------------------------------------"

  # Remove temp file
  rm bodytemp.md
done
