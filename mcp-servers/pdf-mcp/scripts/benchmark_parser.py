"""Reproduce selected-page parser measurements in the chosen parser's environment.

Each measurement includes conversion/model preparation after imports. It is not
an accuracy benchmark and does not compare identical devices unless configured so.
"""

import argparse
import json
import os
import time
from importlib.metadata import version
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("engine", choices=["docling", "marker"])
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, default=3)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-model-download", action="store_true")
    args = parser.parse_args()
    if not args.allow_model_download:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
    proxy = os.getenv("PDF_MCP_PROXY_URL")
    if proxy:
        os.environ["HTTP_PROXY"] = proxy
        os.environ["HTTPS_PROXY"] = proxy
    if args.page < 1 or not 1 <= args.repeat <= 10:
        parser.error("Use a positive page and 1–10 repeats")
    if args.engine == "docling":
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=PdfPipelineOptions(
                        do_ocr=False, do_table_structure=True, document_timeout=120
                    )
                )
            }
        )

        def convert():
            result = converter.convert(args.pdf, page_range=(args.page, args.page))
            return result.document.export_to_dict()
    else:
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict

        converter = PdfConverter(
            artifact_dict=create_model_dict(),
            renderer="marker.renderers.json.JSONRenderer",
            config={
                "page_range": [args.page - 1],
                "disable_ocr": True,
                "disable_tqdm": True,
                "use_llm": False,
            },
        )

        def convert():
            return converter(str(args.pdf)).model_dump(mode="json")

    times = []
    for _ in range(args.repeat):
        start = time.monotonic()
        result = convert()
        times.append(round(time.monotonic() - start, 3))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result))
    print(
        json.dumps(
            {
                "engine": args.engine,
                "version": version("docling" if args.engine == "docling" else "marker-pdf"),
                "source": args.pdf.name,
                "page": args.page,
                "ocr": False,
                "model_download_opt_in": args.allow_model_download,
                "seconds": times,
                "output": str(args.output),
            }
        )
    )


if __name__ == "__main__":
    main()
