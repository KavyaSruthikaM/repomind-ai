from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs"}
IGNORED_DIR_NAMES = {
    "node_modules",
    "dist",
    "build",
    ".git",
    "venv",
    "__pycache__",
    ".next",
    "coverage",
    "repos",
    "chroma_db",
}
LAYER_FOLDER_HINTS: dict[str, tuple[str, ...]] = {
    "middleware": ("middleware", "middlewares"),
    "controller": ("controllers", "controller"),
    "service": ("services", "service"),
    "model": ("models", "model", "schemas", "entities"),
    "route": ("routes", "routers", "api", "endpoints"),
    "database": ("db", "database", "databases", "prisma", "migrations", "repositories"),
}

EXPRESS_ROUTE_RE = re.compile(
    r"(?:router|app)\.(get|post|put|patch|delete|use)\(\s*['\"`]([^'\"`]+)['\"`]",
    re.IGNORECASE,
)
FASTAPI_ROUTE_RE = re.compile(
    r"@(?:router|app)\.(get|post|put|patch|delete)\(\s*[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)
NEXT_ROUTE_RE = re.compile(r"(?:app/api|pages/api)/[^\s'\"]+\.(?:ts|js)x?")
PYTHON_IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE)
JS_IMPORT_RE = re.compile(
    r"(?:import\s+.*?from\s+['\"]([^'\"]+)['\"]|require\(\s*['\"]([^'\"]+)['\"]\s*\))",
    re.MULTILINE,
)


class ArchitectureAnalyzer:
    def analyze(self, repo_path: Path, files: list[str]) -> dict[str, Any]:
        repo_path = repo_path.resolve()
        rel_files = [self._to_relative(repo_path, f) for f in files]
        rel_files = [f for f in rel_files if f and not self._is_ignored_path(f)]

        directories = self._extract_directories(repo_path, rel_files)
        entities = self._extract_entities(rel_files)
        routes = self._extract_routes(repo_path, rel_files)
        middleware = [e for e in entities if e["layer"] == "middleware"]
        controllers = [e for e in entities if e["layer"] == "controller"]
        services = [e for e in entities if e["layer"] == "service"]
        models = [e for e in entities if e["layer"] == "model"]
        database_layers = [e for e in entities if e["layer"] == "database"]
        dependencies = self._extract_dependencies(repo_path, rel_files, entities)
        technologies = self._detect_technologies(rel_files, repo_path)
        mermaid = self._build_mermaid(
            directories=directories,
            entities=entities,
            routes=routes,
            dependencies=dependencies,
        )

        return {
            "directories": directories,
            "entities": entities,
            "routes": routes,
            "middleware": middleware,
            "controllers": controllers,
            "service_entities": services,
            "models": models,
            "database_layers": database_layers,
            "dependencies": dependencies,
            "technologies": technologies,
            "mermaid": mermaid,
            # backward-compatible fields for summary UI
            "project_structure": self._project_structure(rel_files),
            "api_routes": [f"{r['method']} {r['path']}" for r in routes],
            "services": [e["path"] for e in services],
            "database_interactions": self._database_interactions(database_layers, rel_files),
            "major_modules": [
                {"module": e["name"], "responsibility": f"{e['layer']} module at {e['path']}"}
                for e in entities[:30]
            ],
            "dependency_relationships": [
                f"{edge['from']} -> {edge['to']} ({edge['kind']})" for edge in dependencies[:40]
            ],
            "request_data_flow": self._infer_request_flow(routes, entities, dependencies),
        }

    def _to_relative(self, repo_path: Path, file_path: str) -> str:
        path = Path(file_path)
        try:
            return str(path.resolve().relative_to(repo_path.resolve())).replace("\\", "/")
        except ValueError:
            normalized = file_path.replace("\\", "/")
            repo_name = repo_path.name
            marker = f"/{repo_name}/"
            if marker in normalized:
                return normalized.split(marker, 1)[1]
            return normalized.lstrip("/")

    def _is_ignored_path(self, rel_path: str) -> bool:
        parts = rel_path.split("/")
        return any(part in IGNORED_DIR_NAMES for part in parts)

    def _extract_directories(self, repo_path: Path, rel_files: list[str]) -> list[str]:
        found: set[str] = set()
        prefix_counts: dict[str, int] = defaultdict(int)
        for rel in rel_files:
            parts = Path(rel).parts
            if len(parts) < 2:
                continue
            found.add(parts[0])
            found.add(f"{parts[0]}/{parts[1]}")
            for i in range(1, len(parts)):
                prefix_counts["/".join(parts[:i])] += 1
        for child in repo_path.iterdir():
            if child.is_dir() and child.name not in IGNORED_DIR_NAMES:
                found.add(child.name)
        qualified = {
            directory
            for directory in found
            if directory not in IGNORED_DIR_NAMES and (prefix_counts.get(directory, 0) > 0 or (repo_path / directory).is_dir())
        }
        return sorted(qualified)

    def _infer_layer(self, rel_path: str) -> str:
        lower = rel_path.lower().replace("\\", "/")
        for layer, hints in LAYER_FOLDER_HINTS.items():
            if any(f"/{hint}/" in lower or lower.startswith(f"{hint}/") or f"/{hint}." in lower for hint in hints):
                return layer
        if lower.endswith("middleware.ts") or lower.endswith("middleware.js"):
            return "middleware"
        if "route" in Path(rel_path).stem.lower():
            return "route"
        return "module"

    def _extract_entities(self, rel_files: list[str]) -> list[dict[str, str]]:
        entities: list[dict[str, str]] = []
        seen: set[str] = set()
        for rel in rel_files:
            if Path(rel).suffix.lower() not in CODE_EXTENSIONS:
                continue
            layer = self._infer_layer(rel)
            name = Path(rel).stem
            entity_id = rel
            if entity_id in seen:
                continue
            seen.add(entity_id)
            entities.append(
                {
                    "id": entity_id,
                    "name": name,
                    "path": rel,
                    "layer": layer,
                }
            )
        return entities

    def _extract_routes(self, repo_path: Path, rel_files: list[str]) -> list[dict[str, str]]:
        routes: list[dict[str, str]] = []
        seen: set[str] = set()
        for rel in rel_files:
            full = repo_path / rel
            if full.suffix.lower() not in CODE_EXTENSIONS or not full.is_file():
                continue
            try:
                text = full.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for method, path in EXPRESS_ROUTE_RE.findall(text):
                key = f"{method.upper()}:{path}:{rel}"
                if key in seen:
                    continue
                seen.add(key)
                routes.append(
                    {
                        "method": method.upper(),
                        "path": path,
                        "framework": "express",
                        "file": rel,
                    }
                )

            for method, path in FASTAPI_ROUTE_RE.findall(text):
                key = f"{method.upper()}:{path}:{rel}"
                if key in seen:
                    continue
                seen.add(key)
                routes.append(
                    {
                        "method": method.upper(),
                        "path": path,
                        "framework": "fastapi",
                        "file": rel,
                    }
                )

            if NEXT_ROUTE_RE.search(rel):
                route_path = "/" + rel.replace("app", "", 1).replace("pages", "", 1)
                route_path = route_path.rsplit(".", 1)[0]
                key = f"GET:{route_path}:{rel}"
                if key not in seen:
                    seen.add(key)
                    routes.append(
                        {
                            "method": "GET",
                            "path": route_path,
                            "framework": "nextjs",
                            "file": rel,
                        }
                    )
        return routes

    def _extract_dependencies(
        self,
        repo_path: Path,
        rel_files: list[str],
        entities: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        entity_by_stem: dict[str, list[str]] = defaultdict(list)
        for entity in entities:
            entity_by_stem[Path(entity["path"]).stem].append(entity["id"])

        edges: list[dict[str, str]] = []
        seen_edges: set[str] = set()

        for rel in rel_files:
            full = repo_path / rel
            if full.suffix.lower() not in CODE_EXTENSIONS or not full.is_file():
                continue
            try:
                text = full.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            imports: set[str] = set()
            for match in PYTHON_IMPORT_RE.findall(text):
                mod = match[0] or match[1]
                if mod:
                    imports.add(mod.split(".")[-1])
            for match in JS_IMPORT_RE.findall(text):
                mod = match[0] or match[1]
                if mod.startswith("."):
                    resolved = (full.parent / mod).resolve()
                    try:
                        rel_target = str(resolved.relative_to(repo_path.resolve())).replace("\\", "/")
                        imports.add(Path(rel_target).stem)
                    except ValueError:
                        imports.add(Path(mod).stem)
                else:
                    imports.add(Path(mod).name.replace(".js", "").replace(".ts", ""))

            for imported in imports:
                targets = entity_by_stem.get(imported, [])
                for target in targets:
                    if target == rel:
                        continue
                    key = f"{rel}->{target}"
                    if key in seen_edges:
                        continue
                    seen_edges.add(key)
                    edges.append({"from": rel, "to": target, "kind": "import"})

        return edges[:120]

    def _detect_technologies(self, rel_files: list[str], repo_path: Path) -> list[str]:
        detected: set[str] = set()
        lower = [f.lower() for f in rel_files]
        if any("package.json" in f for f in lower):
            detected.add("Node.js")
        if any("next.config" in f for f in lower):
            detected.add("Next.js")
        if any(f.endswith((".tsx", ".ts")) for f in lower):
            detected.add("TypeScript")
        pkg = repo_path / "package.json"
        if pkg.is_file():
            pkg_text = pkg.read_text(encoding="utf-8", errors="ignore").lower()
            if "express" in pkg_text:
                detected.add("Express")
            if "react" in pkg_text:
                detected.add("React")
        if any(f.endswith(".py") for f in lower):
            detected.add("Python")
        if any("fastapi" in f or "/api/" in f for f in lower):
            detected.add("FastAPI")
        if any("prisma" in f for f in lower):
            detected.add("Prisma")
        if any("mongoose" in f for f in lower):
            detected.add("Mongoose")
        if any("supabase" in f for f in lower):
            detected.add("Supabase")
        if any("chroma" in f for f in lower):
            detected.add("ChromaDB")
        return sorted(detected)

    def _project_structure(self, rel_files: list[str]) -> dict[str, list[str]]:
        buckets: dict[str, list[str]] = defaultdict(list)
        for rel in rel_files:
            top = rel.split("/")[0] if "/" in rel else rel
            buckets[top].append(rel)
        return {k: sorted(v)[:40] for k, v in sorted(buckets.items())}

    def _database_interactions(self, database_layers: list[dict[str, str]], rel_files: list[str]) -> list[str]:
        lines = [f"{item['name']} ({item['path']})" for item in database_layers[:12]]
        lower = [f.lower() for f in rel_files]
        if any("chroma" in f for f in lower):
            lines.append("ChromaDB vector store usage detected")
        if any("supabase" in f for f in lower):
            lines.append("Supabase auth/data client detected")
        return lines or ["No explicit database layer files detected"]

    def _infer_request_flow(
        self,
        routes: list[dict[str, str]],
        entities: list[dict[str, str]],
        dependencies: list[dict[str, str]],
    ) -> list[str]:
        flow: list[str] = []
        for route in routes[:5]:
            flow.append(f"{route['method']} {route['path']} handled in {route['file']}")
        for edge in dependencies[:5]:
            flow.append(f"{edge['from']} imports {edge['to']}")
        if not flow and entities:
            flow.append(f"Core module entry: {entities[0]['path']}")
        return flow

    def _safe_id(self, value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_]", "_", value)

    def _build_mermaid(
        self,
        directories: list[str],
        entities: list[dict[str, str]],
        routes: list[dict[str, str]],
        dependencies: list[dict[str, str]],
    ) -> str:
        lines: list[str] = ["flowchart TB"]
        lines.append('classDef route fill:#2a1f4d,stroke:#6f5bd6,color:#efe8ff;')
        lines.append('classDef middleware fill:#1f2a44,stroke:#4f6ea8,color:#dce3ff;')
        lines.append('classDef controller fill:#1f3444,stroke:#4f8ea8,color:#dce3ff;')
        lines.append('classDef service fill:#1f4434,stroke:#4fa88e,color:#dce3ff;')
        lines.append('classDef model fill:#44341f,stroke:#a88e4f,color:#ffe9c7;')
        lines.append('classDef database fill:#0e2230,stroke:#2f5974,color:#d7f0ff;')
        lines.append('classDef module fill:#141a2d,stroke:#3b456d,color:#dce3ff;')

        node_ids: dict[str, str] = {}

        def register_node(key: str, label: str, class_name: str) -> str:
            node_id = self._safe_id(key)
            if node_id[0].isdigit():
                node_id = f"n_{node_id}"
            safe_label = label.replace('"', "'")[:60]
            if node_id not in node_ids:
                lines.append(f'{node_id}["{safe_label}"]:::{class_name}')
                node_ids[node_id] = class_name
            return node_id

        # Directory subgraphs with actual modules inside.
        for directory in directories[:10]:
            dir_entities = [
                entity
                for entity in entities
                if entity["path"] == directory
                or entity["path"].startswith(f"{directory}/")
            ]
            if not dir_entities:
                continue
            subgraph_id = self._safe_id(directory)
            lines.append(f'subgraph {subgraph_id} ["{directory}"]')
            for entity in dir_entities[:14]:
                layer = entity["layer"]
                class_name = (
                    layer
                    if layer in {"route", "middleware", "controller", "service", "model", "database"}
                    else "module"
                )
                register_node(entity["id"], entity["name"], class_name)
            lines.append("end")

        for route in routes[:20]:
            route_id = register_node(
                f"route::{route['file']}::{route['method']}::{route['path']}",
                f"{route['method']} {route['path']}",
                "route",
            )
            file_id = register_node(route["file"], Path(route["file"]).name, "route")
            lines.append(f"{route_id} --> {file_id}")

        for edge in dependencies[:40]:
            from_id = register_node(edge["from"], Path(edge["from"]).name, "module")
            to_id = register_node(edge["to"], Path(edge["to"]).name, "module")
            lines.append(f"{from_id} --> {to_id}")

        if len(node_ids) <= 1:
            # Fallback only when nothing detected.
            for directory in directories[:6]:
                register_node(directory, directory, "module")

        return "\n".join(lines)
