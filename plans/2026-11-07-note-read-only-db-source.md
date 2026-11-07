# Note: read the source tables through a read-only database user, not from exported CSVs

Status: idea, Arda, 2026-11-07. Not decided, not built. A row in `decisions.md` makes it a decision.

## Today

The build reads a folder of CSV files (`--original`, default `data/proving-ground/data/health`), every column as text. A real data provider would have to export its tables to CSV and hand the files over before anything is protected.

## The idea

The data provider creates a database user for the tool with read-only rights on the named tables. No export, no upload. The tool reads the tables, applies the contract (detect, select, protect, repair, score, attack, refuse or release) and only the protected release goes to the researcher. The raw tables never become files that travel.

## What has to be true for "the data never leaves"

The tool must run inside the provider's own environment: their server, or a project in their cloud. If the tool runs on our machine with their database credential, the raw rows still leave the provider; they leave over a database connection instead of in a file. So the deployment is: the tool at the provider, the credential stays there, the release is the only thing that crosses the boundary.

## What it would take

One source adapter. Today the source is a CSV folder; a database connection is a second source behind the same interface, and everything downstream (detect onwards) stays as it is. Not for this weekend's build unless the demo wants to show it.

Security: the user is read-only, scoped to the named tables, its credential lives in the provider's secret store and never in this repo or in a config file we ship.
