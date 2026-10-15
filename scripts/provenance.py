"""Dependency hash usable from standard Python and Blender's Python."""
import json,hashlib
from model import digest
def source_hash(root):
 facts={p:json.loads((root/p).read_text()) for p in ['design/design-spec.json','manual/source/steps.json','manual/source/references.json']}
 facts['generator_sources']={str(p.relative_to(root)):p.read_text() for p in sorted((root/'scripts').glob('*.py'))}
 facts['requirements']=(root/'requirements.txt').read_text()
 facts['pipeline_sources']={str(p.relative_to(root)):p.read_text() for folder in ['pattern-drafting/source','3d-rendering/source','3d-rendering/scripts','docs/source'] for p in sorted((root/folder).rglob('*')) if p.is_file() and p.suffix in ['.json','.py','.in']}
 facts['avatar_assets']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'3d-rendering/assets').rglob('*')) if p.is_file()}
 return digest(facts)
