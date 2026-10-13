#!/usr/bin/env bash
# The fixture project, without SPECAUDIT_ARCH.md.
cp -r "$(dirname "$0")/../_fixtures/arch-project/." .
bash "$(dirname "$0")/../_fixtures/arch-repo.sh" --no-arch
