import os
import json
from datetime import datetime, timezone
import  uuid
from os.path import exists

INPUT_DIR= "../Data"
OUTPUT_DIR= "../OUTPUT"
OUTPUT_FILE="Normalised_doc.json"
os.makedirs(OUTPUT_DIR,exist_ok=True)
output_file_path=os.path.join(OUTPUT_DIR,OUTPUT_FILE)

DOC_METADATA = {
    "Company Overview.txt": {
        "doc_type": "COMPANY_OVERVIEW",
        "entities_expected": ["Person", "Organization", "Product", "Location"],
        "relationships_expected": [
            "FOUNDED", "WORKS_FOR", "PREVIOUSLY_WORKED_AT",
            "DEVELOPED", "LOCATED_IN"
        ]
    },
    "Partnership Announcement.txt": {
        "doc_type": "PARTNERSHIP_PRESS_RELEASE",
        "entities_expected": ["Organization", "Product"],
        "relationships_expected": ["PARTNERED_WITH"]
    },
    "Product Launch.txt": {
        "doc_type": "PRODUCT_LAUNCH",
        "entities_expected": ["Organization", "Product", "Person"],
        "relationships_expected": [
            "DEVELOPED", "WORKS_FOR", "PREVIOUSLY_WORKED_AT"
        ]
    },
    "Leadership Changes.txt": {
        "doc_type": "LEADERSHIP_CHANGE",
        "entities_expected": ["Person", "Organization"],
        "relationships_expected": [
            "WORKS_FOR", "PREVIOUSLY_WORKED_AT"
        ]
    },
    "Research Collaboration.txt": {
        "doc_type": "RESEARCH_COLLABORATION",
        "entities_expected": ["Organization", "Person"],
        "relationships_expected": ["PARTNERED_WITH", "WORKS_FOR"]
    },
    "Market Expansion.txt": {
        "doc_type": "MARKET_EXPANSION",
        "entities_expected": ["Organization", "Person", "Location"],
        "relationships_expected": [
            "WORKS_FOR", "LOCATED_IN"
        ]
    },
    "Technology Partnership.txt": {
        "doc_type": "TECHNOLOGY_PARTNERSHIP",
        "entities_expected": ["Organization", "Product", "Person"],
        "relationships_expected": [
            "PARTNERED_WITH", "DEVELOPED"
        ]
    },
    "Competetive Landscape.txt": {
        "doc_type": "COMPETITIVE_ANALYSIS",
        "entities_expected": ["Organization", "Product", "Person"],
        "relationships_expected": [
            "DEVELOPED", "WORKS_FOR"
        ]
    }
}

def generate_doc_id():
    return f"DOC_{uuid.uuid4().hex[:6]}"

def utc_now():
    return datetime.utcnow().isoformat()+"Z"

def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

documents=[]

def generate_json_docs():
    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith(".txt"):
            continue
        meta = DOC_METADATA.get(filename)
        if not meta:
            raise ValueError(f"No Metadata found for {filename}")
        text = load_text(os.path.join(INPUT_DIR, filename))
        documents.append({
            "doc_id": generate_doc_id(),
            "source_file": filename,
            "doc_type": meta["doc_type"],
            "created_at": utc_now(),
            "text": text,
            "entities_expected": meta["entities_expected"],
            "relationships_expected": meta["relationships_expected"],
        })

    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"Converted {len(documents)} documents to {OUTPUT_FILE} in JSON format")


if __name__ == "__main__":
    generate_json_docs()

