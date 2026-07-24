import ast
import sys
from dataclasses import dataclass
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
_STDLIB = set(sys.stdlib_module_names)

# Inward-only dependency direction (API -> Infrastructure -> Application -> Ports/Domain).
# For each layer, the set of other src layers it is permitted to import from. A layer may
# always import from itself; `config` is the settings leaf, consumed only where noted.
_ALLOWED_LAYER_IMPORTS: dict[str, set[str]] = {
    "domain": set(),  # Domain imports nothing from any other layer.
    "shared": set(),  # ContractModel base — a leaf.
    "config": set(),  # Settings — a leaf.
    "ports": {"domain", "shared"},
    "application": {"domain", "ports", "shared"},
    "infrastructure": {"domain", "ports", "shared", "application", "config"},
    "api": {"domain", "ports", "shared", "application", "infrastructure", "config"},
    "main": {"domain", "ports", "shared", "application", "infrastructure", "config", "api"},
}

# Layers that must stay free of any third-party framework (stdlib only).
_FRAMEWORK_FREE_LAYERS = {"domain", "ports"}

# Third-party packages a layer must never import (in addition to the framework-free rule).
_FORBIDDEN_THIRD_PARTY: dict[str, set[str]] = {
    # Use cases orchestrate; they never touch the ORM, a session, the driver, or the web framework.
    "application": {"sqlalchemy", "asyncpg", "fastapi", "starlette"},
    # The wire base carries only pydantic.
    "shared": {"sqlalchemy", "asyncpg", "fastapi", "starlette", "injector"},
}


@dataclass(frozen=True)
class _Module:
    path: Path
    layer: str
    src_imports: frozenset[str]  # imported src.* layers, excluding own layer
    third_party: frozenset[str]  # imported non-stdlib top-level packages


def _layer_of_path(path: Path) -> str:
    relative = path.relative_to(_SRC)
    return "main" if relative.parts[0] == "main.py" else relative.parts[0]


def _layer_of_module(module: str) -> str | None:
    parts = module.split(".")
    if len(parts) < 2 or parts[0] != "src":
        return None
    return "main" if parts[1] == "main" else parts[1]


def _imported_module_names(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            # Relative imports stay within the same package, so they cannot cross a layer.
            if node.level == 0 and node.module is not None:
                names.append(node.module)
        elif isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
    return names


def _module(path: Path) -> _Module:
    layer = _layer_of_path(path)
    src_imports: set[str] = set()
    third_party: set[str] = set()
    for module in _imported_module_names(ast.parse(path.read_text())):
        top = module.split(".")[0]
        if top == "src":
            imported_layer = _layer_of_module(module)
            if imported_layer is not None and imported_layer != layer:
                src_imports.add(imported_layer)
        elif top != "__future__" and top not in _STDLIB:
            third_party.add(top)
    return _Module(path=path, layer=layer, src_imports=frozenset(src_imports), third_party=frozenset(third_party))


def _all_modules() -> list[_Module]:
    return [_module(path) for path in sorted(_SRC.rglob("*.py")) if path.name != "__init__.py"]


def _relative(path: Path) -> str:
    return str(path.relative_to(_SRC.parent))


class TestLayerDependencies:
    def test_every_source_file_belongs_to_a_known_layer(self):
        unknown = [_relative(module.path) for module in _all_modules() if module.layer not in _ALLOWED_LAYER_IMPORTS]

        assert not unknown, f"Source files in an unrecognised top-level layer (add it to the architecture rules): {unknown}"

    def test_dependencies_point_inward_only(self):
        violations: list[str] = []
        for module in _all_modules():
            allowed = _ALLOWED_LAYER_IMPORTS.get(module.layer, set())
            for imported_layer in sorted(module.src_imports):
                if imported_layer not in allowed:
                    violations.append(f"{_relative(module.path)}  ({module.layer} -> {imported_layer})")

        assert not violations, "Clean Architecture dependency direction violated (dependencies must point inward):\n  " + "\n  ".join(
            violations
        )


class TestFrameworkPurity:
    def test_domain_and_ports_are_framework_free(self):
        violations: list[str] = []
        for module in _all_modules():
            if module.layer in _FRAMEWORK_FREE_LAYERS and module.third_party:
                violations.append(f"{_relative(module.path)} imports {sorted(module.third_party)}")

        assert not violations, "Domain and Ports must be free of any third-party framework (stdlib only):\n  " + "\n  ".join(violations)

    def test_forbidden_third_party_imports(self):
        violations: list[str] = []
        for module in _all_modules():
            forbidden = _FORBIDDEN_THIRD_PARTY.get(module.layer, set()) & module.third_party
            if forbidden:
                violations.append(f"{_relative(module.path)} imports forbidden {sorted(forbidden)}")

        assert not violations, "A layer imported a framework it must not depend on:\n  " + "\n  ".join(violations)

    def test_application_never_imports_a_session_or_orm(self):
        """Use cases orchestrate ports and never touch an AsyncSession or the ORM directly."""
        offenders = [
            _relative(module.path) for module in _all_modules() if module.layer == "application" and "sqlalchemy" in module.third_party
        ]

        assert not offenders, f"Application must not import sqlalchemy (use cases receive no session): {offenders}"
