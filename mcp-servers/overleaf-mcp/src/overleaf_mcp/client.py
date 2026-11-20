"""Bounded Overleaf HTTP calls. Cookies never leave the configured instance."""

import json
import re
from contextlib import closing
import time
from urllib.parse import urljoin, urlsplit

import httpx

from .models import OverleafError, origin


class Client:
    def __init__(self, config, credentials, http=None):
        self.config, self.credentials = config, credentials
        self.http = http or httpx.Client(
            proxy=config.proxy, trust_env=False, follow_redirects=False
        )

    def request(
        self, method, route, body=None, credential=None, output=False, timeout=45, max_bytes=None
    ):
        base = self.config.base_url + "/"
        url = urljoin(base, route)
        allowed = self.config.cdn_origins if output else {self.config.origin}
        if origin(url) not in allowed:
            raise OverleafError(
                "ORIGIN_NOT_ALLOWED", "Remote URL is outside configured service/output origins"
            )
        cred = credential or self.credentials.read()
        started = time.monotonic()
        max_bytes = max_bytes or (80_000_000 if output else 8_000_000)
        for hop in range(6):
            remaining = timeout - (time.monotonic() - started)
            if remaining <= 0:
                raise OverleafError(
                    "TIMEOUT" if method == "GET" else "REQUEST_OUTCOME_UNKNOWN",
                    "Request time budget exceeded",
                )
            dest_origin = origin(url)
            if dest_origin not in allowed:
                raise OverleafError(
                    "ORIGIN_NOT_ALLOWED", "Redirect destination is outside configured origins"
                )
            headers = {}
            payload = body
            if dest_origin == self.config.origin:
                headers["Cookie"] = cred.cookie
                if method != "GET":
                    headers["X-CSRF-Token"] = cred.csrf_token
                    payload = {"_csrf": cred.csrf_token, **(body or {})}
            # A standalone Request does not merge the client's cookie jar on CDN hops.
            request = httpx.Request(
                method,
                url,
                headers=headers,
                json=payload if method != "GET" else None,
                extensions={"timeout": httpx.Timeout(min(remaining, timeout)).as_dict()},
            )
            try:
                with closing(
                    self.http.send(request, stream=True, follow_redirects=False)
                ) as response:
                    status = response.status_code
                    if status in (301, 302, 303, 307, 308):
                        target = urljoin(url, response.headers.get("location", ""))
                        if dest_origin == self.config.origin and "/login" in urlsplit(target).path:
                            raise OverleafError(
                                "AUTH_EXPIRED", "Overleaf redirected the session to login"
                            )
                        if method != "GET":
                            raise OverleafError(
                                "REQUEST_OUTCOME_UNKNOWN",
                                "Mutation returned a redirect; it was not retried",
                            )
                        if not response.headers.get("location"):
                            raise OverleafError("API_SCHEMA", "Redirect has no destination")
                        url = target
                        continue
                    if status == 401:
                        raise OverleafError(
                            "AUTH_EXPIRED"
                            if dest_origin == self.config.origin
                            else "OUTPUT_ACCESS_FAILED",
                            "Service rejected access to this resource",
                        )
                    if status == 403:
                        raise OverleafError(
                            "FORBIDDEN"
                            if dest_origin == self.config.origin
                            else "OUTPUT_ACCESS_FAILED",
                            "Resource access was rejected; this does not prove an expired session",
                        )
                    if status == 429:
                        raise OverleafError(
                            "RATE_LIMITED",
                            "Overleaf rate limit reached; request was not blindly retried",
                            retry_after=response.headers.get("retry-after"),
                        )
                    if status >= 400:
                        raise OverleafError(
                            "REQUEST_OUTCOME_UNKNOWN"
                            if method != "GET" and status >= 500
                            else "HTTP_ERROR",
                            "Remote request failed",
                            http_status=status,
                        )
                    length = response.headers.get("content-length", "")
                    if length.isdigit() and int(length) > max_bytes:
                        raise OverleafError("DOWNLOAD_LIMIT", "Response exceeds byte budget")
                    data = []
                    size = 0
                    for chunk in response.iter_bytes(65536):
                        size += len(chunk)
                        if size > max_bytes:
                            raise OverleafError("DOWNLOAD_LIMIT", "Response exceeds byte budget")
                        if time.monotonic() - started > timeout:
                            raise OverleafError(
                                "TIMEOUT" if method == "GET" else "REQUEST_OUTCOME_UNKNOWN",
                                "Response exceeded the operation deadline",
                            )
                        data.append(chunk)
                    return b"".join(data)
            except httpx.TimeoutException:
                raise OverleafError(
                    "TIMEOUT" if method == "GET" else "REQUEST_OUTCOME_UNKNOWN",
                    "Network timeout; mutations were not retried",
                ) from None
            except httpx.HTTPError:
                raise OverleafError(
                    "NETWORK_ERROR" if method == "GET" else "REQUEST_OUTCOME_UNKNOWN",
                    "Network request failed; mutation outcome may be unknown",
                ) from None
        raise OverleafError("REDIRECT_LIMIT", "Too many download redirects")

    def json(self, method, route, body=None, credential=None, timeout=45):
        data = self.request(method, route, body, credential, timeout=timeout)
        if not data:
            return {}
        try:
            return json.loads(data)
        except (ValueError, UnicodeError):
            raise OverleafError("API_SCHEMA", "Expected JSON but received another format") from None

    def projects(self, credential=None):
        data = self.json("GET", "user/projects", credential=credential)
        if not isinstance(data, dict) or not isinstance(data.get("projects"), list):
            raise OverleafError(
                "API_SCHEMA", "Project list response has changed; an empty list was not assumed"
            )
        result = []
        for p in data["projects"]:
            ident = p.get("_id") or p.get("id")
            if not ident or not isinstance(p.get("name"), str):
                raise OverleafError("API_SCHEMA", "Project identity/name is missing")
            result.append({**p, "id": ident})
        return result

    def csrf(self, credential):
        value = self.request("GET", "dev/csrf", credential=credential).decode("utf-8").strip()
        if not value or "<" in value or len(value) > 8192 or "\n" in value:
            raise OverleafError("API_SCHEMA", "CSRF endpoint did not return a token")
        return value

    def outputs(self, response, filename, project_id=None):
        choices = [f for f in response.get("outputFiles", []) if f.get("path") == filename]
        if len(choices) != 1 or not isinstance(choices[0].get("url"), str):
            raise OverleafError(
                "OUTPUT_NOT_AVAILABLE", "Requested file is not uniquely present in this build"
            )
        url = choices[0]["url"]
        encoded_project = re.search(r"/project/([^/]+)/", urlsplit(url).path)
        if project_id and encoded_project and encoded_project[1] != project_id:
            raise OverleafError(
                "OUTPUT_PROJECT_MISMATCH", "Output reference belongs to another project"
            )
        domain = response.get("pdfDownloadDomain")
        if domain:
            if origin(domain) not in self.config.cdn_origins:
                raise OverleafError(
                    "ORIGIN_NOT_ALLOWED",
                    "Build output origin is not configured; no credential was sent there",
                )
            url = urljoin(domain.rstrip("/") + "/", url.lstrip("/"))
            request = httpx.URL(url).copy_merge_params(
                {
                    "compileGroup": response.get("compileGroup", ""),
                    "clsiserverid": response.get("clsiServerId", ""),
                    "enable_pdf_caching": "true",
                }
            )
            url = str(request)
        return self.request("GET", url, output=True)
