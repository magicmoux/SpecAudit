#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
# The fixture project, without SPECAUDIT_ARCH.md.
cp -r "$(dirname "$0")/../_fixtures/arch-project/." .
bash "$(dirname "$0")/../_fixtures/arch-repo.sh" --no-arch
