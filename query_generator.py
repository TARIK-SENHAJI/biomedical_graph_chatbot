import json
import time
import config

def generate_multiple_cypher_queries(client, question, analysis, conversation_history=None,
                                     model_option="Auto (tries multiple)"):

    if analysis["query_strategy"] == "no_graph_needed" or not analysis["entities"]:
        return []

    context = _build_conversation_context(conversation_history)

    # Prepare entity information for query generation
    entities_text = ", ".join(analysis["entities"])
    aspects_text = "\n".join([f"- {aspect}" for aspect in analysis["aspects"]])

    prompt = f"""You are a Neo4j Cypher expert. Based on the deep analysis, generate multiple targeted Cypher queries.

{context}

Original question: "{question}"

Deep analysis results:
- Entities identified: {entities_text}
- Aspects to explore:
{aspects_text}
- Query strategy: {analysis["query_strategy"]}
- Reasoning: {analysis["reasoning"]}

Database schema:
- Nodes: Source (with 'name' property) and Destination (with 'name' property)
- Relations: TO (with 'type' property)
- Structure: (n:Source)-[r:TO]->(m:Destination)

Your task: Generate MULTIPLE Cypher queries to comprehensively answer the question.

Query generation rules:
1. Create separate queries for each major entity or aspect
2. Use bidirectional searches to find all connections: both (n)-[r]->(m) and (m)-[r]->(n)
3. Use CONTAINS for flexible matching (case-insensitive with toLower)
4. Limit each query to {config.MAX_QUERY_RESULTS} results for performance
5. Each query should target a specific aspect identified in the analysis

Query templates:

Template 1 - Single entity exploration (bidirectional):
MATCH (n:Source)-[r:TO]->(m:Destination)
WHERE toLower(n.name) CONTAINS 'entity_name' OR toLower(m.name) CONTAINS 'entity_name'
RETURN n, r, m
LIMIT {config.MAX_QUERY_RESULTS}

Template 2 - Two-entity interaction:
MATCH (n:Source)-[r:TO]->(m:Destination)
WHERE (toLower(n.name) CONTAINS 'entity1' AND toLower(m.name) CONTAINS 'entity2')
   OR (toLower(n.name) CONTAINS 'entity2' AND toLower(m.name) CONTAINS 'entity1')
RETURN n, r, m
LIMIT {config.MAX_QUERY_RESULTS}

Template 3 - Entity with specific relationship type:
MATCH (n:Source)-[r:TO]->(m:Destination)
WHERE toLower(n.name) CONTAINS 'entity_name' AND toLower(r.type) CONTAINS 'relationship'
RETURN n, r, m
LIMIT {config.MAX_QUERY_RESULTS}

Respond with queries in this JSON format:
{{
  "queries": [
    {{
      "purpose": "Description of what this query explores",
      "cypher": "MATCH (n:Source)..."
    }},
    {{
      "purpose": "Description of another aspect",
      "cypher": "MATCH (n:Source)..."
    }}
  ]
}}

Generate 1-4 queries depending on complexity. Be strategic and comprehensive.
RESPOND WITH ONLY VALID JSON, NO MARKDOWN, NO EXPLANATIONS OUTSIDE JSON.
"""

    messages = [{'role': 'user', 'content': prompt}]
    models_to_try = _get_models_list(model_option)

    for model in models_to_try:
        try:
            response = client.chat.complete(
                model=model,
                messages=messages,
                temperature=config.QUERY_GENERATION_TEMPERATURE
            )
            queries_text = response.choices[0].message.content.strip()

            # Clean up response
            queries_text = _extract_json(queries_text)

            # Parse JSON
            queries_data = json.loads(queries_text)
            return queries_data.get("queries", [])

        except Exception as e:
            if model == models_to_try[-1]:
                return []
            time.sleep(1)
            continue


def _build_conversation_context(conversation_history):
    # Build context string from recent conversation history
    if not conversation_history or len(conversation_history) <= 1:
        return ""

    recent_messages = conversation_history[-config.RECENT_MESSAGES_FOR_CONTEXT:]
    context = "Recent conversation:\n"
    for msg in recent_messages:
        content = msg['content'][:200]
        context += f"{msg['role']}: {content}\n"
    context += "\n"
    return context


def _extract_json(text):
    # Extract and clean JSON from markdown code blocks or raw text
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text


def _get_models_list(model_option):
    # Return list of models to try based on selected option
    if model_option == "Auto (tries multiple)":
        return config.DEFAULT_MODELS
    else:
        return [model_option]