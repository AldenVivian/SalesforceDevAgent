# context/mcp_tools.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from ingestion.auth import sf_manager
from context.tool_cache import cache


class GetApexClassInput(BaseModel):
    name: str = Field(..., description="Apex class name")


def get_apex_class(inp: GetApexClassInput) -> Dict[str, Any]:
    key = f"apex_class:{inp.name}"
    cached = cache.get(key)
    if cached:
        return cached
    sf = sf_manager.client()
    res = sf.toolingexecute(
        "query",
        params={
            "q": f"SELECT Id, Name, Body FROM ApexClass WHERE Name = '{inp.name}' LIMIT 1"
        },
    )
    records = res.get("records", [])
    out = records[0] if records else {}
    cache.set(key, out, ttl=300)
    return out


class SearchMetadataInput(BaseModel):
    q: Optional[str] = Field(None, description="Name contains filter")
    types: Optional[List[str]] = None


def search_metadata(inp: SearchMetadataInput) -> Dict[str, Any]:
    # Example using Tooling for classes/triggers; extend for other types.
    sf = sf_manager.client()
    terms = inp.q or ""
    results = {}
    soqls = {
        "ApexClass": f"SELECT Id, Name FROM ApexClass WHERE Name LIKE '%{terms}%' LIMIT 100",
        "ApexTrigger": f"SELECT Id, Name, TableEnumOrId FROM ApexTrigger WHERE Name LIKE '%{terms}%' LIMIT 100",
    }
    for t, q in soqls.items():
        results[t] = sf.toolingexecute("query", params={"q": q}).get("records", [])
    return results


class GetObjectSchemaInput(BaseModel):
    object_api_name: str


def get_object_schema(inp: GetObjectSchemaInput) -> Dict[str, Any]:
    key = f"describe:{inp.object_api_name}"
    cached = cache.get(key)
    if cached:
        return cached
    sf = sf_manager.client()
    res = sf.restful(f"sobjects/{inp.object_api_name}/describe")
    cache.set(key, res, ttl=600)
    return res
