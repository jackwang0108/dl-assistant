"""Bound the complete JSON response, with continuation inside oversized records."""

import base64
import json

from .models import WARNING, PdfError, digest


def bounded(document_id, records, scope, max_chars=24000, cursor=None):
    if not 2000 <= max_chars <= 100000:
        raise PdfError("INVALID_BUDGET", "max_chars must be 2000–100000")
    signature = digest([document_id, scope, max_chars])
    index = offset = 0
    if cursor:
        try:
            if len(cursor) > 2048:
                raise ValueError()
            state = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            if state["signature"] != signature:
                raise ValueError()
            index, offset = state["index"], state["offset"]
            if (
                type(index) is not int
                or type(offset) is not int
                or not 0 <= index <= len(records)
                or offset < 0
            ):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            raise PdfError(
                "INVALID_CURSOR", "Cursor does not match this document, request and budget"
            ) from None
    response = {
        "document_id": document_id,
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
            raise PdfError("INVALID_CURSOR", "Cursor offset is outside the record")
        if offset == 0 and used + len(raw) <= capacity:
            response["items"].append(records[index])
            used += len(raw) + 2
            index += 1
            continue
        if response["items"]:
            break
        # JSON string escaping can at most multiply these source characters by six.
        take = max(1, capacity // 6)
        fragment = raw[offset : offset + take]
        final = offset + len(fragment) >= len(raw)
        response["items"].append(
            {
                "kind": "record_fragment",
                "record_index": index,
                "offset": offset,
                "encoding": "json",
                "text": fragment,
                "final": final,
            }
        )
        if final:
            index, offset = index + 1, 0
        else:
            offset += len(fragment)
        break
    if index < len(records):
        response["truncated"] = True
        response["next_cursor"] = base64.urlsafe_b64encode(
            json.dumps({"signature": signature, "index": index, "offset": offset}).encode()
        ).decode()
    if len(json.dumps(response, ensure_ascii=False)) > max_chars:
        raise PdfError("RESPONSE_BUDGET", "Response metadata exceeds budget")
    return response
