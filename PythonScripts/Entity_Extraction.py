import  json
import os
import  uuid
import  openai
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("MY_OPENAI_KEY")
openai.api_key = OPENAI_API_KEY

normalised_json_file = "OUTPUT/Normalised_doc.json"
output_entities_file = "OUTPUT/Entity_Extraction.json"

def generate_entity_id(entity):
    return f"{entity[:3].upper()}_{uuid.uuid4().hex[:6]}"

def canonical_person(name):
    titles = ["Dr.", "CEO", "CTO", "VP", "Founder", "CRO"]
    titles_found = [t for t in titles if t in name]
    clean_name=name
    for t in titles_found:
        clean_name = clean_name.replace(t, "").strip()
    return clean_name,",".join(titles_found) if titles_found else ""

def canonical_org(name):
    suffixes = ["Inc.", "Ltd.", "LLC", "Corporation"]
    for s in suffixes:
        if name.endswith(s):
            name=name.replace(s, "").strip()
    return name

def entity_extraction_prompt(document_text):
    prompt = f"""
        You are a structured entity extractor.
        Given the text below, extract all entities of the following types:
        - Person (include title if present)
        - Organization (include type if obvious)
        - Product
        - Location (City, State, Country)

        Return ONLY JSON in the exact format below:

        {{
          "people": [{{"name": "", "title": ""}}],
          "organizations": [{{"name": "", "type": ""}}],
          "products": [{{"name": "", "domain": ""}}],
          "locations": [{{"name": "", "type": ""}}]
        }}

        Do NOT include relationships. Do NOT guess. Only extract explicit mentions.
        Text:
        \"\"\"
        {document_text}
        \"\"\"
        """
    return prompt


def load_normalised_json(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        normalised_json = json.load(f)
    return normalised_json

def extraction_loop(json_file):
    entities=[]
    docs_file = load_normalised_json(json_file)
    for doc in docs_file:
        text = doc["text"]
        prompt = entity_extraction_prompt(text)
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        try:
            raw_entities = json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error parsing JSON for {doc['doc_id']}:{e}")
            continue

        canonical_entities={"people":[],"organizations":[],"products":[],"locations":[]}

        #People
        for p in raw_entities.get("people", []):
            name,title = canonical_person(p["name"])
            canonical_entities["people"].append({
                "entity_id":generate_entity_id("PER"),
                "title":title or p.get("title",""),
                "name":name,
                "type":"Person",
                "source_doc":doc["doc_id"]
            })
        # Organizations
        for o in raw_entities.get("organizations", []):
            name = canonical_org(o["name"])
            canonical_entities["organizations"].append({
                "entity_id": generate_entity_id("ORG"),
                "name": name,
                "type": "Organization",
                "source_doc": doc["doc_id"]
            })

        # Products
        for pr in raw_entities.get("products", []):
            canonical_entities["products"].append({
                "entity_id": generate_entity_id("PRO"),
                "name": pr["name"],
                "type": "Product",
                "source_doc": doc["doc_id"]
            })

    # Locations
        for l in raw_entities.get("locations", []):
            canonical_entities["locations"].append({
                "entity_id": generate_entity_id("LOC"),
                "name": l["name"],
                "type": l.get("type", "Location"),
                "source_doc": doc["doc_id"]
            })

        entities.append({
            "doc_id": doc["doc_id"],
            "source_file": doc["source_file"],
            "entities": canonical_entities
        })

        with open(output_entities_file,"w",encoding="utf-8") as f:
            json.dump(entities,f,ensure_ascii=False,indent=4)


if __name__ == "__main__":
    extraction_loop(normalised_json_file)






