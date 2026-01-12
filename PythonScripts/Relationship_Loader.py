from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
Entity_File = "OUTPUT/Relationship_Extraction.json"

driver = GraphDatabase.driver(NEO4J_URI,auth=(NEO4J_USER,NEO4J_PASSWORD))

def ingest_relationships(relations_extraction_json_file):
    with open(relations_extraction_json_file, "r", encoding="utf-8") as f:
        relationships = json.load(f)

    with driver.session() as session:
        for r in relationships:
            cypher=f"""
                MATCH(a:{r["source_type"]} {{name:$source}})
                MATCH(b:{r["target_type"].split(",")[0].strip().replace(" ","_")} {{name:$target}})
                MERGE (a)-[rel:{r["relation"]}]->(b)
            """
            session.run(cypher,source=r["source"],target=r["target"])

if __name__ == "__main__":
    ingest_relationships("OUTPUT/Relationship_Extraction.json")