import sys

from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
Entity_File = "OUTPUT/Entity_Extraction.json"

driver = GraphDatabase.driver(NEO4J_URI,auth=(NEO4J_USER,NEO4J_PASSWORD))

def ingest_entities(entity_file):
    with open(entity_file, "r", encoding="utf-8") as f:
        docs = json.load(f)
    with driver.session() as session:
        for doc in docs:
            entities = doc["entities"]
            for person in entities["people"]:
                session.run("""
                    MERGE (p:Person {entity_id: $id})
                    SET p.name = $name,
                    p.title = $title
                """, id=person["entity_id"], name=person["name"], title=person.get("title",""))

            for org in entities["organizations"]:
                session.run("""
                    MERGE (o:Organization {entity_id: $id})
                    SET o.name = $name,
                    o.type = $type
                """, id=org["entity_id"], name=org["name"], type=org["type"])

            for prod in entities["products"]:
                session.run("""
                    MERGE (p:Product {entity_id:$id})
                    SET p.name=$name
                """, id=prod["entity_id"],
                     name=prod["name"])

            for loc in entities["locations"]:
                session.run("""
                    MERGE (l:Location {entity_id:$id})
                    SET l.name=$name, l.type=$type
                """, id=loc["entity_id"],
                     name=loc["name"],
                     type=loc.get("type","Location"))

    print("Nodes ingested successfully")

if __name__ == "__main__":
    ingest_entities(Entity_File)

