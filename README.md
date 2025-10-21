# Breast Cancer Knowledge Graph Chatbot

An **AI chatbot** that interacts with a **Neo4j knowledge graph** specialized in breast cancer.  
It converts natural language questions into **Cypher queries** to retrieve precise biological and medical information.

## Features

- Answer complex biological/medical questions with evidence-based responses.
- Conversation history support.
- Automatic fallback to an alternative model for higher reliability.
- Interactive **Streamlit** interface.

## Pipeline

The chatbot processes questions in **5 main steps**:

1. **Classification**  
   Decide if the question requires a knowledge graph search or can be answered directly.

2. **Deep Analysis**  
   Identify entities (genes, proteins, etc.), aspects, and build a query plan.

3. **Query Generation**  
   Generate one or more targeted Cypher queries.

4. **Query Execution**  
   Execute queries on Neo4j and collect results.

5. **Synthesis**  
   Aggregate results and generate a coherent answer.

## Example Questions

- What genes are associated with breast cancer?  
- How does BRCA1 interact with DNA repair pathways?  
- What drugs target HER2?  

## Installation

```bash
git clone <REPO_URL>
cd breast-cancer-chatbot
streamlit run app.py
