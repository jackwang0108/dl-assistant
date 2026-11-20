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
    assert opened["actual_version"] in source
    doc = service.document(opened["document_id"])
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
