"""Upload the KB corpus to S3 for the Bedrock Knowledge Base (impact-explainer TASK-2).

For each .txt in corpus/, uploads the document and a sidecar `<file>.metadata.json` in the
Bedrock-expected format so the KB attaches title/sourceUrl/documentType/visaTypeTags as
retrievable metadata. Idempotent (re-upload overwrites). Run from repo root:

    python scripts/upload_corpus.py

Env: AWS_REGION (default us-east-2), KB_BUCKET (default visatrack-kb-documents-<acct>-ue2).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

CORPUS = Path(__file__).resolve().parent.parent / "corpus"
REGION = os.environ.get("AWS_REGION", "us-east-2")
BUCKET = os.environ.get("KB_BUCKET", "visatrack-kb-documents-782989862515-ue2")


def _aws(*args: str) -> None:
    subprocess.run(["aws", *args], check=True)


def main() -> None:
    manifest = json.loads((CORPUS / "manifest.json").read_text())
    for txt in sorted(CORPUS.glob("*.txt")):
        meta = manifest.get(txt.name)
        if not meta:
            print(f"[skip] no manifest entry for {txt.name}")
            continue

        # Bedrock KB sidecar metadata format.
        sidecar = {
            "metadataAttributes": {
                "title": {"value": {"type": "STRING", "stringValue": meta["title"]}, "includeForEmbedding": True},
                "sourceUrl": {"value": {"type": "STRING", "stringValue": meta["sourceUrl"]}, "includeForEmbedding": False},
                "documentType": {"value": {"type": "STRING", "stringValue": meta["documentType"]}, "includeForEmbedding": True},
                "visaTypeTags": {"value": {"type": "STRING_LIST", "stringListValue": meta["visaTypeTags"]}, "includeForEmbedding": True},
            }
        }
        sidecar_path = txt.with_suffix(txt.suffix + ".metadata.json")
        sidecar_path.write_text(json.dumps(sidecar, indent=2))

        _aws("s3", "cp", str(txt), f"s3://{BUCKET}/{txt.name}", "--region", REGION)
        _aws("s3", "cp", str(sidecar_path), f"s3://{BUCKET}/{sidecar_path.name}", "--region", REGION)
        print(f"[ok] uploaded {txt.name} (+metadata)")

    print(f"\nDone. Corpus in s3://{BUCKET}/ (region {REGION}).")
    print("Next: create the Bedrock Knowledge Base pointing at this bucket, then sync.")


if __name__ == "__main__":
    main()
