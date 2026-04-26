# GitHub Distribution

This repository can be published to a personal or organization GitHub repository and used as the distribution source for the AIP Codex plugin.

## Publisher Flow

1. Create an empty GitHub repository.
2. Add it as the `origin` remote:

```bash
git remote add origin https://github.com/jzjwonderful/ai-implementation-protocol.git
```

3. Push the repository:

```bash
git push -u origin master
```

4. Create a release when the plugin is ready for a stable version:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## User Install Flow

Users install the plugin by cloning the repository and running the installer:

```bash
git clone https://github.com/jzjwonderful/ai-implementation-protocol.git
cd ai-implementation-protocol
python scripts/install_codex_plugin.py
```

On Windows PowerShell, the same flow is:

```powershell
git clone https://github.com/jzjwonderful/ai-implementation-protocol.git
Set-Location ai-implementation-protocol
python .\scripts\install_codex_plugin.py
```

The installer copies:

```text
plugins/ai-implementation-protocol/
```

to:

```text
~/plugins/ai-implementation-protocol/
```

and updates:

```text
~/.agents/plugins/marketplace.json
```

with a local marketplace entry for the plugin.

## Updating An Existing Install

After pulling a newer version, users can replace the installed plugin:

```bash
git pull
python scripts/install_codex_plugin.py --force
```

## Verification

After installation, confirm these files exist:

```text
~/plugins/ai-implementation-protocol/.codex-plugin/plugin.json
~/.agents/plugins/marketplace.json
```

Then restart Codex or refresh the plugin list and use the `aip` skill.
