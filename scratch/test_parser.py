
import sys
from pathlib import Path

# Add the backend to sys.path so we can import TreeSitterParser
sys.path.append("/Users/kavyasruthikam/Downloads/RepoMind AI")

from backend.parser.tree_sitter_parser import TreeSitterParser

parser = TreeSitterParser()

# Test Python
python_code = """
class AuthService:
    def login(self, username, password):
        pass
    
    def register(self, email, password):
        pass
    
    def verify_token(self, token):
        pass

def helper():
    pass
"""

python_file = Path("/Users/kavyasruthikam/Downloads/RepoMind AI/scratch/test.py")
python_file.write_text(python_code)

# Test JS
js_code = """
class AuthService {
    login(username, password) {
    }
    
    register(email, password) {
    }
    
    verify_token(token) {
    }
}

function helper() {
}
"""
js_file = Path("/Users/kavyasruthikam/Downloads/RepoMind AI/scratch/test.js")
js_file.write_text(js_code)

# Test TS
ts_code = """
class AuthService {
    public login(username: string, password: string): void {
    }
    
    async register(email: string, password: string): Promise<void> {
    }
    
    private verify_token(token: string): boolean {
        return true;
    }
}
"""
ts_file = Path("/Users/kavyasruthikam/Downloads/RepoMind AI/scratch/test.ts")
ts_file.write_text(ts_code)

print("--- Python ---")
result = parser.parse_file(python_file)
chunks, routes, rels = result["chunks"], result["routes"], result.get("relationships", [])
for c in chunks:
    print(f"Chunk: {c.get('entity_type')}, Name: {c.get('name')}")
for r in routes:
    print(f"Route: {r['method']} {r['path']} -> {r['handler']}")
for rel in rels:
    print(f"Relationship: {rel['from']} {rel['relationship']} {rel['to']}")

print("\n--- JavaScript ---")
result = parser.parse_file(js_file)
chunks, routes, rels = result["chunks"], result["routes"], result.get("relationships", [])
for c in chunks:
    print(f"Chunk: {c.get('entity_type')}, Name: {c.get('name')}")
for r in routes:
    print(f"Route: {r['method']} {r['path']} -> {r['handler']}")
for rel in rels:
    print(f"Relationship: {rel['from']} {rel['relationship']} {rel['to']}")

print("\n--- TypeScript ---")
result = parser.parse_file(ts_file)
chunks, routes = result["chunks"], result["routes"]
for c in chunks:
    print(f"Chunk: {c.get('entity_type')}, Name: {c.get('name')}")
for r in routes:
    print(f"Route: {r['method']} {r['path']} -> {r['handler']}")
