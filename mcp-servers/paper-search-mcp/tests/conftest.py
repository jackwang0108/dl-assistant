import httpx
import pytest

from paper_search_mcp.config import Config
from paper_search_mcp.service import Service
from paper_search_mcp.transport import Transport

SS_PAPER = {
    "paperId": "s1",
    "externalIds": {"ArXiv": "1706.03762", "DOI": "10.1234/attention"},
    "title": "Attention Is All You Need",
    "authors": [{"authorId": "a1", "name": "John Smith"}, {"authorId": "a2", "name": "Jane Smith"}],
    "year": 2017,
    "publicationDate": "2017-06-12",
    "abstract": "The complete abstract",
    "venue": "NeurIPS",
    "citationCount": 100,
    "openAccessPdf": {"url": "https://papers.test/paper.pdf"},
}

OA_PAPER = {
    "id": "https://openalex.org/W1",
    "doi": "https://doi.org/10.1234/attention",
    "display_name": "Attention Is All You Need",
    "publication_year": 2017,
    "publication_date": "2017-12-01",
    "authorships": [{"author": {"id": "https://openalex.org/A1", "display_name": "John Smith"}}],
    "abstract_inverted_index": {"OpenAlex": [0], "abstract": [1]},
    "cited_by_count": 80,
    "open_access": {"is_oa": True},
    "locations": [{"pdf_url": "https://papers.test/paper.pdf"}],
}

SCHOLAR_PAPER = {
    "result_id": "result1",
    "title": "Attention Is All You Need",
    "link": "https://papers.test/landing",
    "snippet": "Partial text",
    "publication_info": {
        "summary": "J Smith - NeurIPS, 2017 - papers.test",
        "authors": [{"name": "J Smith"}],
    },
    "inline_links": {"cited_by": {"cites_id": "12345", "total": 120}},
    "resources": [{"file_format": "PDF", "link": "https://papers.test/paper.pdf"}],
}

ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"
 xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
 xmlns:arxiv="http://arxiv.org/schemas/atom">
 <opensearch:totalResults>1</opensearch:totalResults><entry>
 <id>http://arxiv.org/abs/1706.03762v1</id><title>Attention Is All You Need</title>
 <published>2017-06-12T00:00:00Z</published><updated>2017-06-13T00:00:00Z</updated>
 <summary>arXiv full abstract</summary><author><name>John Smith</name></author>
 <category term="cs.CL"/><arxiv:doi>10.1234/attention</arxiv:doi>
 </entry></feed>"""


@pytest.fixture
def make_service(tmp_path):
    def make(handler, keys=None):
        intervals = dict.fromkeys(
            ["arxiv", "semantic_scholar", "scholar", "openalex", "download"], 0.0
        )
        return Service(
            Config(tmp_path, keys or {"scholar": "fake-secret", "openalex": "fake-key"}),
            Transport(
                httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True),
                intervals,
            ),
        )

    return make
