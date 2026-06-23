# Verification

## Commands Run

1. `python scripts/aip.py --help`
2. `python scripts/aip.py init --repo-root C:\Users\jzjwo\AppData\Local\Temp\aip-router-verify-20260426`
3. `python scripts/aip.py start 2026-04-26-router-sample --title "Router verification" --repo-root C:\Users\jzjwo\AppData\Local\Temp\aip-router-verify-20260426`
4. `python scripts/aip.py resume --repo-root C:\Users\jzjwo\AppData\Local\Temp\aip-router-verify-20260426`
5. `python scripts/aip.py check --repo-root C:\Users\jzjwo\AppData\Local\Temp\aip-router-verify-20260426`
6. `python plugins/ai-implementation-protocol/scripts/aip.py init --repo-root C:\Users\jzjwo\AppData\Local\Temp\aip-plugin-router-verify-20260426`
7. `python plugins/ai-implementation-protocol/scripts/aip.py start 2026-04-26-plugin-router-sample --title "Plugin router verification" --repo-root C:\Users\jzjwo\AppData\Local\Temp\aip-plugin-router-verify-20260426`
8. `python plugins/ai-implementation-protocol/scripts/aip.py resume --repo-root C:\Users\jzjwo\AppData\Local\Temp\aip-plugin-router-verify-20260426`
9. `python plugins/ai-implementation-protocol/scripts/aip.py check --repo-root C:\Users\jzjwo\AppData\Local\Temp\aip-plugin-router-verify-20260426`
10. `python scripts/aip.py check --repo-root .`

## Results

- Root `aip.py --help` listed `init`, `start`, `resume`, and `check`.
- Root router initialized a temporary repository.
- Root router created a feature package.
- Root router printed the expected resume summary.
- Root router `check` passed.
- Plugin-packaged router initialized a separate temporary repository using plugin-packaged templates.
- Plugin-packaged router created a feature package.
- Plugin-packaged router printed the expected resume summary.
- Plugin-packaged router `check` passed.
- Repository-local `python scripts/aip.py check --repo-root .` passed after closeout.

## Not Run

- Real Codex UI invocation of `$aip`.
- Alias execution in the terminal CLI, because aliases are intentionally skill-level routing rules.

## Known Risks

- Codex must pass the user's text after `$aip` through to the skill context for routing. The skill now documents exactly how to interpret that text.
