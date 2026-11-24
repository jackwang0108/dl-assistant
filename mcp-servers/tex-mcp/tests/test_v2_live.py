"""Opt-in fixed-version imports from real arXiv; no TeX compilation or paid API."""

import os
from pathlib import Path

import pytest

from tex_mcp.models import Limits
from tex_mcp.service import Service

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.getenv("TEX_MCP_RUN_LIVE") != "1", reason="Set TEX_MCP_RUN_LIVE=1"),
]


@pytest.mark.parametrize(
    "source,label", [("1706.03762v7", "fig:model-arch"), ("1512.03385v1", "fig:block")]
)
def test_real_paper_source_references_and_picture(tmp_path, source, label):
    service = Service(tmp_path / "cache")
    opened = service.open(source, limits=Limits(max_seconds=80, max_requests=4))
    assert opened["actual_version"] == "v" + source.rsplit("v", 1)[1]
    document_id = opened["document_id"]
    doc = service.document(document_id)
    obj = service.object(doc, label)
    payload = service.object_payload(doc, obj, "images")
    assert any(
        a.get("image_status") == "ready" and Path(a["image_path"]).exists()
        for a in payload["assets"]
    )
    assert doc["references"] and any(r["cited_at"] for r in doc["references"].values())
    referenced = next(e for e in doc["edges"] if e.get("target") == obj["object_id"])
    page = service.read(
        opened["document_id"], section=referenced["section_id"], asset_mode="images"
    )
    items = page["items"]
    while page["next_cursor"]:
        page = service.read(
            opened["document_id"],
            section=referenced["section_id"],
            asset_mode="images",
            cursor=page["next_cursor"],
        )
        items += page["items"]
    assert any(i["kind"] == "object" and i["object_id"] == obj["object_id"] for i in items)

    def read_edge(edge):
        matches = service.search(document_id, edge["key"], section=edge["section_id"])["matches"]
        hit = next(m for m in matches if edge["start"] <= m["start"] < edge["end"])
        params = {"match_ref": hit["match_ref"], "context_chars": 120, "asset_mode": "images"}
        page = service.read(document_id, **params)
        assert page["items"][0]["match_range"] == [hit["start"], hit["end"]]
        assert page["items"][0]["scope"] == "match"
        records = list(page["items"])
        while page["next_cursor"]:
            page = service.read(document_id, **params, cursor=page["next_cursor"])
            records.extend(page["items"])
        assert any(i["kind"] == "body" and i["source_locations"] for i in records)
        return records

    local_figure = next(i for i in read_edge(referenced) if i.get("object_id") == obj["object_id"])
    assert any(a.get("image_status") == "ready" for a in local_figure["assets"])
    citation = next(
        e
        for e in doc["edges"]
        if e["kind"] == "citation"
        and e["command"] != "nocite"
        and doc["references"].get(e["key"], {}).get("status") == "parsed"
    )
    assert any(
        i["kind"] == "reference" and i["key"] == citation["key"] for i in read_edge(citation)
    )
