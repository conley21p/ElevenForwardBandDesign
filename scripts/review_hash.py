"""Print the source fingerprint; never auto-approve the impact record."""
from build import source_hash,ROOT
print(source_hash(ROOT))
