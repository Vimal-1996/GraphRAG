import json

import  openai
import  os

from PythonScripts.Relationship_Loader import driver

OPENAI_API_KEY = os.getenv("MY_OPENAI_KEY")
openai.api_key = OPENAI_API_KEY

def entity_resolution_prompt(user_query):
    return f"""
    Identity the entities mentioned in the query.
    Allowed Entity types:
        Person, Organization, Product, Location
    Return Only JSON:
    [
        {{"name:","type":""}}
    ]
    
    Query:
    "{user_query}"
    """

def resolve_query_entities(query):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user","content":entity_resolution_prompt(query)}],
        temperature=0
    )
    return json.loads(response.choices[0].message.content)

def fetch_subgraph(entity):
    with driver.session() as session:

        # ---------------- PERSON CENTERED ----------------
        if entity["type"] == "Person":
            result = session.run("""
                MATCH (p:Person {name:$name})
                OPTIONAL MATCH (p)-[:FOUNDED]->(o:Organization)
                OPTIONAL MATCH (p)-[:WORKS_FOR]->(org:Organization)
                OPTIONAL MATCH (p)-[:PREVIOUSLY_WORKED_AT]->(prev:Organization)
                OPTIONAL MATCH (p)-[:APPOINTED_AS]->(roleOrg:Organization)
                RETURN p,
                       collect(DISTINCT o) AS founded_orgs,
                       collect(DISTINCT org) AS current_orgs,
                       collect(DISTINCT prev) AS previous_orgs,
                       collect(DISTINCT roleOrg) AS appointed_orgs
            """, name=entity["name"])

        # ---------------- ORGANIZATION CENTERED ----------------
        elif entity["type"] == "Organization":
            result = session.run("""
                MATCH (o:Organization {name:$name})
                OPTIONAL MATCH (p:Person)-[:FOUNDED]->(o)
                OPTIONAL MATCH (o)-[:DEVELOPED]->(pr:Product)
                OPTIONAL MATCH (o)-[:PARTNERED_WITH]->(partner:Organization)
                OPTIONAL MATCH (o)-[:LOCATED_IN]->(l:Location)
                RETURN o,
                       collect(DISTINCT p) AS founders,
                       collect(DISTINCT pr) AS products,
                       collect(DISTINCT partner) AS partners,
                       collect(DISTINCT l) AS locations
            """, name=entity["name"])

        # ---------------- PRODUCT CENTERED ----------------
        elif entity["type"] == "Product":
            result = session.run("""
                MATCH (pr:Product {name:$name})
                OPTIONAL MATCH (o:Organization)-[:DEVELOPED]->(pr)
                OPTIONAL MATCH (pr)-[:APPROVED_BY]->(regulator:Organization)
                OPTIONAL MATCH (pr)-[:USED_BY]->(userOrg:Organization)
                RETURN pr,
                       collect(DISTINCT o) AS developers,
                       collect(DISTINCT regulator) AS approved_by,
                       collect(DISTINCT userOrg) AS users
            """, name=entity["name"])

        # ---------------- LOCATION CENTERED ----------------
        elif entity["type"] == "Location":
            result = session.run("""
                MATCH (l:Location {name:$name})
                OPTIONAL MATCH (o:Organization)-[:LOCATED_IN]->(l)
                OPTIONAL MATCH (p:Person)-[:WORKS_FOR]->(o)-[:LOCATED_IN]->(l)
                RETURN l,
                       collect(DISTINCT o) AS organizations,
                       collect(DISTINCT p) AS people
            """, name=entity["name"])

        else:
            return []

        return result.data()


def build_context(graph_data):
    context = []

    for row in graph_data:

        # ---------------- PERSON-CENTERED ----------------
        if "p" in row:
            person = row["p"]["name"]

            for o in row.get("founded_orgs", []):
                context.append(f"{person} founded {o['name']}.")

            for o in row.get("current_orgs", []):
                context.append(f"{person} works for {o['name']}.")

            for o in row.get("previous_orgs", []):
                context.append(f"{person} previously worked at {o['name']}.")

            for o in row.get("appointed_orgs", []):
                context.append(f"{person} was appointed at {o['name']}.")

        # ---------------- ORGANIZATION-CENTERED ----------------
        if "o" in row:
            org = row["o"]["name"]

            for f in row.get("founders", []):
                context.append(f"{f['name']} founded {org}.")

            for p in row.get("products", []):
                context.append(f"{org} developed {p['name']}.")

            for partner in row.get("partners", []):
                context.append(f"{org} partnered with {partner['name']}.")

            for l in row.get("locations", []):
                context.append(f"{org} is located in {l['name']}.")

        # ---------------- PRODUCT-CENTERED ----------------
        if "pr" in row:
            product = row["pr"]["name"]

            for o in row.get("developers", []):
                context.append(f"{o['name']} developed {product}.")

            for r in row.get("approved_by", []):
                context.append(f"{product} was approved by {r['name']}.")

            for u in row.get("users", []):
                context.append(f"{u['name']} uses {product}.")

        # ---------------- LOCATION-CENTERED ----------------
        if "l" in row:
            location = row["l"]["name"]

            for o in row.get("organizations", []):
                context.append(f"{o['name']} is located in {location}.")

            for p in row.get("people", []):
                context.append(f"{p['name']} works in organizations located in {location}.")

    return "\n".join(context)


def answer_prompt(context, question):
    return f"""
        You are an enterprise intelligence assistant.

        Answer ONLY using the facts below.
        If the answer is not present, say "Not found in knowledge graph."

        Facts:
        {context}

        Question:
        {question}
        """
def generate_answer(context, question):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": answer_prompt(context, question)}],
        temperature=0
    )
    return response.choices[0].message.content

def graph_rag_query(question):
    entities = resolve_query_entities(question)

    full_context = []
    for e in entities:
        graph_data = fetch_subgraph(e)
        full_context.append(build_context(graph_data))

    return generate_answer("\n".join(full_context), question)

if __name__ == "__main__":
    print(graph_rag_query(
    "How is Sarah Chen and Marcus Rodriguez related ?"
))


