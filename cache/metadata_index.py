# cache/metadata_index.py
from typing import Dict, List
from ingestion.auth import sf_manager


def list_components(types: List[str]) -> Dict[str, List[str]]:
    sf = sf_manager.client()
    # Using REST proxy for SOAP Metadata is not directly available via simple-salesforce;
    # in practice, use a small helper or external lib to invoke Metadata API listMetadata
    # or rely on Tooling for discoverable types.
    # Placeholder structure to be filled by your Metadata client.
    return {t: [] for t in types}
