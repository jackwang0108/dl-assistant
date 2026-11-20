"""Bounded public HTTP downloads; DNS addresses are checked and pinned per connection."""

import ipaddress
import os
import socket
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from .models import Limits, PdfError


def public_addresses(host):
    try:
        addresses = list(
            dict.fromkeys(
                row[4][0] for row in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            )
        )
    except OSError:
        raise PdfError("NETWORK_DNS", "Could not resolve download host") from None
    if not addresses or any(
        not ipaddress.ip_address(ip).is_global or ipaddress.ip_address(ip).is_multicast
        for ip in addresses
    ):
        raise PdfError("UNSAFE_URL", "Download host must resolve only to public addresses")
    return addresses


class Downloader:
    def __init__(self, client=None, resolver=None, proxy_url=None):
        self.client = client
        self.resolver = resolver or public_addresses
        self.proxy_url = proxy_url or os.getenv("PDF_MCP_PROXY_URL")

    def fetch(self, source, limits=None):
        limits = limits or Limits()
        started, requests, current = time.monotonic(), 0, source
        client = self.client or httpx.Client(
            follow_redirects=False, trust_env=False, proxy=self.proxy_url
        )
        try:
            while requests < limits.max_requests:
                remaining = limits.max_seconds - (time.monotonic() - started)
                if remaining <= 0:
                    raise PdfError("DOWNLOAD_TIMEOUT", "Download time budget exceeded")
                parsed = urlsplit(current)
                if (
                    parsed.scheme not in ("http", "https")
                    or not parsed.hostname
                    or parsed.username
                    or parsed.password
                ):
                    raise PdfError("UNSAFE_URL", "Use a public HTTP(S) URL without credentials")
                if parsed.port not in (None, 80, 443):
                    raise PdfError("UNSAFE_URL", "Only standard HTTP(S) ports are supported")
                if self.proxy_url:
                    # Explicitly trusted proxy resolves destination names (including Clash fake-IP DNS).
                    # It must enforce its own destination network policy; no false claim of direct DNS pinning.
                    hostname = parsed.hostname.lower().rstrip(".")
                    if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
                        raise PdfError("UNSAFE_URL", "Local download hosts are not accepted")
                    try:
                        literal = ipaddress.ip_address(hostname)
                    except ValueError:
                        literal = None
                    if literal and (not literal.is_global or literal.is_multicast):
                        raise PdfError(
                            "UNSAFE_URL", "Private/reserved destination IP is not accepted"
                        )
                    pinned = current
                else:
                    address = self.resolver(parsed.hostname)[0]
                    host = f"[{address}]" if ":" in address else address
                    if parsed.port:
                        host += f":{parsed.port}"
                    pinned = urlunsplit((parsed.scheme, host, parsed.path, parsed.query, ""))
                requests += 1
                try:
                    with client.stream(
                        "GET",
                        pinned,
                        headers={"Host": parsed.netloc},
                        extensions={"sni_hostname": parsed.hostname},
                        timeout=min(remaining, 30),
                    ) as response:
                        if response.is_redirect:
                            location = response.headers.get("location")
                            if not location:
                                raise PdfError("DOWNLOAD_REDIRECT", "Redirect has no destination")
                            target = urljoin(current, location)
                            if parsed.scheme == "https" and urlsplit(target).scheme != "https":
                                raise PdfError("UNSAFE_URL", "HTTPS downgrade redirect rejected")
                            current = target
                            continue
                        if response.status_code in (429, 500, 502, 503, 504):
                            if requests >= limits.max_requests:
                                code = (
                                    "RATE_LIMITED"
                                    if response.status_code == 429
                                    else "HTTP_UNAVAILABLE"
                                )
                                raise PdfError(
                                    code,
                                    "Download server is temporarily unavailable",
                                    http_status=response.status_code,
                                )
                            time.sleep(min(1, max(0, remaining / 4)))
                            continue
                        if response.status_code != 200:
                            raise PdfError(
                                "HTTP_ERROR",
                                "Download request failed",
                                http_status=response.status_code,
                            )
                        length = response.headers.get("content-length", "")
                        if length.isdigit() and int(length) > limits.max_bytes:
                            raise PdfError("DOWNLOAD_SIZE", "Download exceeds byte budget")
                        chunks, size = [], 0
                        for chunk in response.iter_bytes(65536):
                            size += len(chunk)
                            if size > limits.max_bytes:
                                raise PdfError("DOWNLOAD_SIZE", "Download exceeds byte budget")
                            if time.monotonic() - started > limits.max_seconds:
                                raise PdfError("DOWNLOAD_TIMEOUT", "Download time budget exceeded")
                            chunks.append(chunk)
                        return b"".join(chunks), {
                            "requested_url": source,
                            "final_url": current,
                            "requests": requests,
                            "bytes": size,
                            "network_mode": "explicit_trusted_proxy"
                            if self.proxy_url
                            else "public_dns_pinned",
                        }
                except httpx.TimeoutException:
                    raise PdfError("DOWNLOAD_TIMEOUT", "Download connection timed out") from None
                except httpx.HTTPError:
                    raise PdfError("NETWORK_ERROR", "Download connection failed") from None
            raise PdfError("DOWNLOAD_REDIRECT", "Request/redirect budget exceeded")
        finally:
            if self.client is None:
                client.close()
