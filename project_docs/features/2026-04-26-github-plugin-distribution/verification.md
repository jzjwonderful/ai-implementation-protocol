# Verification

## Commands Run

1. `python scripts/install_codex_plugin.py --home C:\Users\jzjwo\AppData\Local\Temp\aip-install-home-20260426`
2. `python scripts/install_codex_plugin.py --home C:\Users\jzjwo\AppData\Local\Temp\aip-install-home-20260426`
3. `python scripts/install_codex_plugin.py --home C:\Users\jzjwo\AppData\Local\Temp\aip-install-home-20260426 --force`
4. Parse installed plugin manifest with PowerShell `ConvertFrom-Json`.
5. Parse installed marketplace with PowerShell `ConvertFrom-Json`.
6. `python scripts/aip_check.py --repo-root .`

## Results

- First install copied the plugin to the temporary home directory.
- First install created `.agents/plugins/marketplace.json` in the temporary home directory.
- Reinstall without `--force` returned exit code `1` and did not replace the existing plugin.
- Reinstall with `--force` returned exit code `0` and replaced the installed plugin.
- Installed `.codex-plugin/plugin.json` parsed as JSON.
- Installed `.agents/plugins/marketplace.json` parsed as JSON.
- Repository-local `python scripts/aip_check.py --repo-root .` passed after closeout.

## Not Run

- GitHub release creation.
- Installation from a remote raw URL.

## Known Risks

- Users need local Git and Python.
- Codex may require a restart or plugin refresh after marketplace changes.
