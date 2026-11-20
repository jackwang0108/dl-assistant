"""Stable result snapshots and whole-response character limits."""

import base64
import json

from .models import WARNING, OverleafError, digest


def page(store, scope, records=None, cursor=None, max_chars=24000):
    if not 2000 <= max_chars <= 100000:
        raise OverleafError("INVALID_BUDGET", "max_chars must be 2000–100000")
    scope = [scope, max_chars]
    index = offset = 0
    if cursor:
        try:
            if len(cursor) > 2048:
                raise ValueError()
            state = json.loads(base64.urlsafe_b64decode(cursor))
            if state["scope"] != digest(scope):
                raise ValueError()
            snapshot_id, index, offset = state["snapshot"], state["index"], state["offset"]
            records = store.read_snapshot(snapshot_id, scope)
            if (
                type(index) is not int
                or type(offset) is not int
                or not 0 <= index <= len(records)
                or offset < 0
            ):
                raise ValueError()
        except (ValueError, TypeError, KeyError):
            raise OverleafError("INVALID_CURSOR", "Cursor scope or state is invalid") from None
    else:
        snapshot_id = store.snapshot(scope, records)
    result = {
        "snapshot_id": snapshot_id,
        "items": [],
        "truncated": False,
        "next_cursor": None,
        "content_warning": WARNING,
    }
    capacity = max_chars - 850
    used = 0
    while index < len(records):
        raw = json.dumps(records[index], ensure_ascii=False)
        if offset > len(raw):
            raise OverleafError("INVALID_CURSOR", "Record offset is outside the snapshot")
        if not offset and used + len(raw) <= capacity:
            result["items"].append(records[index])
            used += len(raw) + 2
            index += 1
            continue
        if result["items"]:
            break
        take = max(1, capacity // 6)
        text = raw[offset : offset + take]
        final = offset + len(text) >= len(raw)
        result["items"].append(
            {
                "kind": "record_fragment",
                "record_index": index,
                "offset": offset,
                "encoding": "json",
                "text": text,
                "final": final,
            }
        )
        if final:
            index, offset = index + 1, 0
        else:
            offset += len(text)
        break
    if index < len(records):
        result["truncated"] = True
        result["next_cursor"] = base64.urlsafe_b64encode(
            json.dumps(
                {"scope": digest(scope), "snapshot": snapshot_id, "index": index, "offset": offset}
            ).encode()
        ).decode()
    if len(json.dumps(result, ensure_ascii=False)) > max_chars:
        raise OverleafError("RESPONSE_BUDGET", "Response exceeds budget")
    return result
