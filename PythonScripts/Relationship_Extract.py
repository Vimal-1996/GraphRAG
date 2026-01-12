import json
import openai
import os
from dotenv import load_dotenv
load_dotenv()
import uuid

OPENAI_API_KEY = os.getenv("MY_OPENAI_KEY")
openai.api_key = OPENAI_API_KEY
relationship_output_file = "OUTPUT/Relationship_Extraction.json"

ALLOWED_RELATIONSHIPS = [
    "FOUNDED",
    "WORKS_FOR",
    "PREVIOUSLY_WORKED_AT",
    "DEVELOPED",
    "PARTNERED_WITH",
    "APPOINTED_AS",
    "COLLABORATES_WITH",
    "APPROVED_BY",
    "LOCATED_IN"
]


def relationship_extraction_prompt(document_text, entity_list):
    return f"""
You are a strict relationship extraction system.

Rules:
- Use ONLY the entities provided
- Use ONLY allowed relationships
- Do NOT create new entities
- Extract ONLY explicitly stated facts
- No inference

Allowed Relationships:
{", ".join(ALLOWED_RELATIONSHIPS)}

Entities:
{json.dumps(entity_list, indent=2)}

Text:
\"\"\"
{document_text}
\"\"\"

Return ONLY JSON in this format:
{{
  "relationships": [
    {{
      "source": "",
      "source_type": "",
      "relation": "",
      "target": "",
      "target_type": ""
    }}
  ]
}}
"""


def flatten_entities(entities):
    flat = []
    for group in entities.values():
        for e in group:
            flat.append({
                "name": e["name"],
                "type": e["type"]
            })
    return flat

def extract_relationships(normalised_file, entity_file):
    with open(normalised_file, "r", encoding="utf-8") as f:
        docs = json.load(f)

    with open(entity_file, "r", encoding="utf-8") as f:
        entity_docs = json.load(f)

    entity_lookup = {d["doc_id"]: d["entities"] for d in entity_docs}

    relationships = []

    for doc in docs:
        doc_id = doc["doc_id"]
        text = doc["text"]

        if doc_id not in entity_lookup:
            continue

        flat_entities = flatten_entities(entity_lookup[doc_id])

        prompt = relationship_extraction_prompt(text, flat_entities)

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        try:
            rel_json = json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Relationship JSON error in {doc_id}: {e}")
            continue

        for r in rel_json.get("relationships", []):
            relationships.append({
                "rel_id": f"REL_{uuid.uuid4().hex[:8]}",
                "doc_id": doc_id,
                "source": r["source"],
                "source_type": r["source_type"],
                "relation": r["relation"],
                "target": r["target"],
                "target_type": r["target_type"]
            })

    with open(relationship_output_file, "w", encoding="utf-8") as f:
        json.dump(relationships, f, indent=4)

    print(f"✅ Step 4 completed — {len(relationships)} relationships extracted")

if __name__=="__main__":
    if __name__ == "__main__":
        normalised_json_file="OUTPUT/Normalised_doc.json"
        output_entities_file="OUTPUT/Entity_Extraction.json"
        extract_relationships(
            normalised_json_file,
            output_entities_file
        )