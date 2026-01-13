An industry-style GraphRAG system that extracts structured knowledge from unstructured documents, builds a knowledge graph in Neo4j, and answers complex business intelligence questions using LLM-powered graph reasoning.

This project demonstrates how modern enterprise intelligence systems combine:

LLMs
Knowledge Graphs
Graph Traversal
Retrieval-Augmented Generation (RAG)

Architectural Overview
=======================

Raw Text Files
      │
      ▼
Document Normalization (JSON)
      │
      ▼
LLM-based Entity & Relationship Extraction
      │
      ▼
Knowledge Graph (Neo4j)
      │
      ▼
Subgraph Retrieval (Entity-centered)
      │
      ▼
LLM Answer Generation (GraphRAG)

