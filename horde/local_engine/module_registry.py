import glob
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from horde.local_engine.models import ModuleDefinition


class ModuleRegistry:
    def __init__(self, modules_dir: Path):
        self.modules_dir = modules_dir
        self._cache: Dict[str, ModuleDefinition] = {}
        self._errors: List[Dict[str, str]] = []
        self.refresh()

    def refresh(self) -> None:
        self._cache.clear()
        self._errors.clear()

        module_files = glob.glob(str(self.modules_dir / "**/*.json"), recursive=True)
        seen_ids: set[str] = set()

        for file_path in module_files:
            rel_path = os.path.relpath(file_path, self.modules_dir)
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    raw_data = json.load(handle)

                module = ModuleDefinition.model_validate(raw_data)

                if module.module_id in seen_ids:
                    self._errors.append(
                        {
                            "file": rel_path,
                            "error": (
                                "Duplicate module_id detected: "
                                f"'{module.module_id}'"
                            ),
                        }
                    )
                    continue

                seen_ids.add(module.module_id)
                self._cache[module.module_id] = module

            except json.JSONDecodeError as exc:
                self._errors.append(
                    {"file": rel_path, "error": f"Invalid JSON: {exc}"}
                )
            except Exception as exc:
                self._errors.append({"file": rel_path, "error": str(exc)})

    def get_module(self, module_id: str) -> Optional[ModuleDefinition]:
        return self._cache.get(module_id)

    def list_modules(self) -> List[Dict[str, Any]]:
        return [module.model_dump() for module in self._cache.values()]

    def list_errors(self) -> List[Dict[str, str]]:
        return list(self._errors)
