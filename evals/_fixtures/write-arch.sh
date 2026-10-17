#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
# Prints a minimal SPECAUDIT_ARCH.md that marks each path given as audited with the formal profile: what
# /spec-audit:init would propose for a repository holding only these documents. /spec-audit:start refuses to run
# without the file, so every script or case that builds a repository to audit writes it first.
# Usage: bash write-arch.sh <path>... > SPECAUDIT_ARCH.md
set -euo pipefail
cat <<'MD'
# SpecAudit architecture

The layout of this repository and the role of each part, as SpecAudit reads it (format: `/spec-audit:init`, or SpecAudit's docs/usage.md). Paths not listed are read-only.

## Paths

| Path | Role | Profile | Description |
|---|---|---|---|
MD
for p in "$@"; do
  printf '| `%s` | audited | formal | specification |\n' "$p"
done
cat <<'MD'

## Oracles

| Path | Kind | Command | Correspondence | Guards |
|---|---|---|---|---|

## Normative dependencies

| Document | Normative |
|---|---|

## Mapped pairs

| Document | Counterpart | Correspondence |
|---|---|---|
MD
