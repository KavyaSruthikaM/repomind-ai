import re
from pathlib import Path
from typing import Any

from tree_sitter import Node
from tree_sitter_languages import get_parser

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "javascript",
}

CLASS_NODE_TYPES = {"class_definition", "class_declaration"}
FUNCTION_NODE_TYPES = {"function_definition", "function_declaration", "method_definition"}
NAME_NODE_TYPES = {"identifier", "type_identifier", "property_identifier"}


class TreeSitterParser:
    def __init__(self, max_chunk_size: int = 2000) -> None:
        self.max_chunk_size = max_chunk_size

    def _detect_language(self, file_path: Path) -> str | None:
        return LANGUAGE_MAP.get(file_path.suffix.lower())

    def _safe_text(self, node: Node, source: bytes) -> str:
        return source[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")

    def _extract_field_name(self, node: Node, source: bytes) -> str | None:
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            name = self._safe_text(name_node, source).strip()
            if name:
                return name[:120]

        for child in node.children:
            if child.type in NAME_NODE_TYPES:
                name = self._safe_text(child, source).strip()
                if name:
                    return name[:120]
        return None

    def _get_node_name(self, node: Node, source: bytes) -> str:
        """Extract a clean symbol name from AST fields, with graceful fallbacks."""
        if node.type in CLASS_NODE_TYPES:
            name = self._extract_field_name(node, source)
            if name:
                return name

            text = self._safe_text(node, source).strip()
            match = re.search(r"\bclass\s+([A-Za-z_][\w]*)", text)
            if match:
                return match.group(1)[:120]

            fallback = text.split("{", 1)[0].split(":", 1)[0].strip()
            if fallback.startswith("class "):
                fallback = fallback[6:].strip()
            return fallback[:120] if fallback else "UnknownClass"

        if node.type in FUNCTION_NODE_TYPES:
            name = self._extract_field_name(node, source)
            if name:
                return name

            text = self._safe_text(node, source).strip()
            for pattern in (
                r"\bdef\s+([A-Za-z_][\w]*)",
                r"\b(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)",
                r"\b([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{",
            ):
                match = re.search(pattern, text)
                if match:
                    return match.group(1)[:120]

            fallback = text.split("{", 1)[0].split(":", 1)[0].strip()
            for prefix in ("async def ", "def ", "function ", "async function "):
                if fallback.startswith(prefix):
                    fallback = fallback[len(prefix) :].split("(", 1)[0].strip()
                    break
            return fallback[:120] if fallback else "UnknownFunction"

        text = self._safe_text(node, source).strip()
        return text.split("{", 1)[0].split(":", 1)[0].strip()[:120]

    def _entity_type(self, node: Node) -> str | None:
        if node.type in FUNCTION_NODE_TYPES:
            return "function"
        if node.type in CLASS_NODE_TYPES:
            return "class"
        return None

    def _extract_methods(self, node: Node, source: bytes) -> list[str]:
        methods: list[str] = []

        def find_methods(current: Node):
            if current.type in FUNCTION_NODE_TYPES:
                name = self._get_node_name(current, source)
                if name:
                    methods.append(name)
                return

            for child in current.children:
                if child.type in CLASS_NODE_TYPES:
                    continue
                find_methods(child)

        body_node = None
        for child in node.children:
            if child.type in {"block", "class_body"}:
                body_node = child
                break

        if body_node:
            for child in body_node.children:
                find_methods(child)
        else:
            for child in node.children:
                find_methods(child)

        return list(dict.fromkeys(methods))  # Maintain order and remove duplicates

    def _chunk_name(self, node: Node, source: bytes) -> str:
        if node.type in CLASS_NODE_TYPES or node.type in FUNCTION_NODE_TYPES:
            return self._get_node_name(node, source)
        text = self._safe_text(node, source).strip()
        return text.split("{", 1)[0].split(":", 1)[0].strip()[:120]

    def _extract_fastapi_route(self, node: Node, source: bytes) -> dict[str, Any] | None:
        if node.type != "decorated_definition":
            return None

        decorator_node = None
        func_node = None
        for child in node.children:
            if child.type == "decorator":
                decorator_node = child
            elif child.type == "function_definition":
                func_node = child

        if not decorator_node or not func_node:
            return None

        decorator_text = self._safe_text(decorator_node, source)
        match = re.search(r"@\w+\.(get|post|put|delete|patch|options|head)\(\s*(['\"])(.*?)\2", decorator_text, re.IGNORECASE)
        if match:
            method = match.group(1).upper()
            path = match.group(3)
            handler = self._get_node_name(func_node, source)
            return {
                "entity_type": "route",
                "method": method,
                "path": path,
                "handler": handler,
                "content": f"FastAPI route: {method} {path} handled by {handler}"
            }
        return None

    def _extract_express_route(self, node: Node, source: bytes) -> dict[str, Any] | None:
        if node.type != "call_expression":
            return None

        text = self._safe_text(node, source)
        match = re.search(r"\w+\.(get|post|put|delete|patch|options|head)\(\s*(['\"])(.*?)\2", text, re.IGNORECASE)
        if match:
            handler = "anonymous"
            arg_list = node.child_by_field_name("arguments")
            if arg_list and len(arg_list.children) > 1:
                for arg in arg_list.children:
                    if arg.type in NAME_NODE_TYPES:
                        handler = self._safe_text(arg, source)
                        break
                    elif arg.type in {"function_expression", "arrow_function"}:
                        handler = "anonymous_function"
                        break

            method = match.group(1).upper()
            path = match.group(3)
            return {
                "entity_type": "route",
                "method": method,
                "path": path,
                "handler": handler,
                "content": f"Express route: {method} {path} handled by {handler}"
            }
        return None

    def _extract_nextjs_route(self, node: Node, source: bytes, file_path: str) -> dict[str, Any] | None:
        if node.type != "export_statement" or ("route" not in file_path.lower()):
            return None

        text = self._safe_text(node, source)
        match = re.search(r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)", text)
        if match:
            method = match.group(1)
            logical_path = "/"
            if "app" in file_path:
                parts = file_path.split("app")[-1].split("/")
                filtered_parts = [p for p in parts if p and not p.endswith((".ts", ".js", "route"))]
                logical_path = "/" + "/".join(filtered_parts)

            return {
                "entity_type": "route",
                "method": method,
                "path": logical_path,
                "handler": method,
                "content": f"Next.js route: {method} {logical_path}"
            }
        return None

    def _extract_imports(self, root_node: Node, source: bytes) -> set[str]:
        symbols: set[str] = set()
        queue = [root_node]
        while queue:
            current = queue.pop(0)
            text = self._safe_text(current, source)
                
            if current.type == "import_statement":
                matches = re.findall(r"\bimport\s+([\w, ]+)", text)
                for m in matches:
                    for name in m.split(","):
                        symbols.add(name.strip().split(" as ")[-1].strip())
                matches = re.findall(r"import\s+([\s\S]*?)\s+from", text)
                if matches:
                    import_clause = matches[0]
                    names = re.findall(r"[\w$]+", import_clause)
                    for n in names:
                        if n not in {"import", "as", "type"}:
                            symbols.add(n)
            elif current.type == "import_from_statement":
                matches = re.findall(r"\bimport\s+([\w, *() \n\t]+)", text)
                for m in matches:
                    m = m.replace("(", "").replace(")", "").replace("*", "")
                    for name in m.split(","):
                        clean_name = name.strip().split(" as ")[-1].strip()
                        if clean_name:
                            symbols.add(clean_name)
            if current.type in CLASS_NODE_TYPES or current.type in FUNCTION_NODE_TYPES:
                name = self._get_node_name(current, source)
                if name and name not in {"UnknownClass", "UnknownFunction"}:
                    symbols.add(name)
            for child in current.children:
                queue.append(child)
        return symbols

    def _extract_relationships(self, node: Node, source: bytes, current_entity: str, symbols: set[str]) -> list[dict[str, Any]]:
        relationships = []
        seen = {current_entity}
        def find_refs(current: Node):
            if current.type in NAME_NODE_TYPES:
                name = self._safe_text(current, source).strip()
                if name in symbols and name not in seen:
                    relationships.append({"from": current_entity, "to": name, "relationship": "uses"})
                    seen.add(name)
            for child in current.children:
                find_refs(child)
        for child in node.children:
            if child.type in {"block", "class_body", "statement_block", "formal_parameters"}:
                find_refs(child)
        return relationships

    def _build_chunk(self, node: Node, source: bytes, path: str, language: str, text: str) -> dict[str, Any]:
        entity_type = self._entity_type(node)

        chunk: dict[str, Any] = {
            "entity_type": entity_type if entity_type else node.type,
            "name": self._get_node_name(node, source) if entity_type else self._chunk_name(node, source),
            "file_path": path,
            "language": language,
            "content": text,
        }

        if entity_type == "class":
            chunk["methods"] = self._extract_methods(node, source)

        return chunk

    def _walk(self, node: Node, source: bytes, path: str, language: str, chunks: list[dict[str, Any]], routes: list[dict[str, Any]], rels: list[dict[str, Any]], symbols: set[str]) -> None:
        # Route detection
        route = None
        if language == "python":
            route = self._extract_fastapi_route(node, source)
        elif language in {"javascript", "typescript"}:
            route = self._extract_express_route(node, source) or self._extract_nextjs_route(node, source, path)

        if route:
            route["file_path"] = path
            route["language"] = language
            routes.append(route)

        interesting_types = {
            "function_definition",
            "class_definition",
            "function_declaration",
            "class_declaration",
            "method_definition",
            "import_statement",
            "import_from_statement",
            "lexical_declaration",
            "export_statement",
            "call_expression",
            "decorated_definition",
        }
        if node.type in interesting_types:
            text = self._safe_text(node, source).strip()
            if text and len(text) <= self.max_chunk_size:
                chunk = self._build_chunk(node, source, path, language, text)
                chunks.append(chunk)
                if chunk.get("entity_type") in {"class", "function"}:
                    rels.extend(self._extract_relationships(node, source, chunk["name"], symbols))

        for child in node.children:
            self._walk(child, source, path, language, chunks, routes, rels, symbols)

    def parse_file(self, file_path: Path) -> dict[str, list[dict[str, Any]]]:
        language = self._detect_language(file_path)
        if not language:
            return {"chunks": [], "routes": [], "relationships": []}
        try:
            parser = get_parser(language if language != "tsx" else "typescript")
            source = file_path.read_bytes()
            tree = parser.parse(source)
        except Exception:
            return {"chunks": [], "routes": [], "relationships": []}

        symbols = self._extract_imports(tree.root_node, source)
        chunks: list[dict[str, Any]] = []
        routes: list[dict[str, Any]] = []
        relationships: list[dict[str, Any]] = []
        self._walk(tree.root_node, source, str(file_path), language, chunks, routes, relationships, symbols)

        if not chunks:
            raw = source.decode("utf-8", errors="ignore")
            if raw.strip():
                chunks.append(
                    {
                        "entity_type": "module",
                        "name": file_path.name,
                        "file_path": str(file_path),
                        "language": language,
                        "content": raw[: self.max_chunk_size],
                    }
                )
        return {"chunks": chunks, "routes": routes, "relationships": relationships}

    def parse_repository(self, repo_path: Path) -> dict[str, list[dict[str, Any]]]:
        all_chunks: list[dict[str, Any]] = []
        all_routes: list[dict[str, Any]] = []
        all_rels: list[dict[str, Any]] = []
        for file_path in repo_path.rglob("*"):
            if file_path.is_file():
                result = self.parse_file(file_path)
                all_chunks.extend(result["chunks"])
                all_routes.extend(result["routes"])
                all_rels.extend(result.get("relationships", []))
        return {"chunks": all_chunks, "routes": all_routes, "relationships": all_rels}
