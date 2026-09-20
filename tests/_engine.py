"""测试共用的路径：引擎 = aip 技能目录（scripts/ 与 templates/ 都在它下面）。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "plugins" / "ai-implementation-protocol" / "skills" / "aip"
SCRIPTS = ENGINE / "scripts"
