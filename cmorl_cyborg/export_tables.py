from __future__ import annotations

import cmorl_minicage.export_tables as base

from .config import load_export_tables_config

base.load_export_tables_config = load_export_tables_config
export_tables = base.export_tables


def main() -> None:
    base.main()


if __name__ == "__main__":
    main()
