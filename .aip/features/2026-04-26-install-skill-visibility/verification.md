# Verification

## Commands Run

1. Inspect `C:\Users\jzjwo\.agents\plugins\marketplace.json`.
2. Inspect `C:\Users\jzjwo\plugins\ai-implementation-protocol\.codex-plugin\plugin.json`.
3. Inspect `C:\Users\jzjwo\plugins\ai-implementation-protocol\skills\aip\SKILL.md`.
4. Inspect `C:\Users\jzjwo\.agents\skills`.
5. `python scripts/install_codex_plugin.py --home C:\Users\jzjwo\AppData\Local\Temp\aip-skill-visible-home-20260426`
6. `python scripts/install_codex_plugin.py --force`
7. `python scripts/aip.py check --repo-root .`

## Results

- Plugin package existed in the expected home plugin directory.
- Marketplace JSON existed and pointed to `./plugins/ai-implementation-protocol`.
- `~/.agents/skills/aip/SKILL.md` was missing before the fix.
- Temporary-home install created plugin package, marketplace, plugin skill, and direct user skill.
- Current-user `--force` reinstall created `C:\Users\jzjwo\.agents\skills\aip\SKILL.md`.
- Installed direct skill contains `$aip init`, `$aip start`, `$aip resume`, and `$aip check`.
- Repository-local `python scripts/aip.py check --repo-root .` passed after closeout.

## Not Run

- Full Codex app restart from this tool session.

## Known Risks

- The user must restart Codex after installing a new skill.
