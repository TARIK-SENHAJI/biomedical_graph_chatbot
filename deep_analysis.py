import json
import time
import config

def deep_analysis_of_question(client, question, conversation_history=None, model_option="Auto (tries multiple)"):

    context = _build_conversation_context(conversation_history)

    prompt = f"""You are an expert biomedical analyst. Perform a DEEP ANALYSIS of this question before any database queries.

{context}

User question: "{question}"

Your task: Analyze this question thoroughly and provide a structured analysis in JSON format.

Think step-by-step:
1. What are ALL the biomedical entities mentioned? (genes, proteins, drugs, pathways, cell types)
2. What relationships or interactions is the user asking about?
3. Are there multiple aspects to this question that require separate queries?
4. What is the logical connection between entities?
5. What information would best answer this question?

Knowledge graph structure reminder:
- Nodes: Source and Destination (both have 'name' property)
- Relations: TO (with 'type' property describing the relationship)
- Contains: genes, proteins, drugs, pathways, molecular interactions

Respond with ONLY valid JSON in this exact format:
{{
  "entities": ["entity1", "entity2", ...],
  "aspects": ["aspect1", "aspect2", ...],
  "relationships_to_explore": ["relationship type 1", "relationship type 2", ...],
  "query_strategy": "single_entity" or "multiple_entities" or "complex_interaction",
  "reasoning": "Brief explanation of your analysis"
}}

Example for "How does HER2 affect MMP9 and other signaling pathways?":
{{
  "entities": ["HER2", "MMP9", "signaling pathways"],
  "aspects": ["HER2 to MMP9 connection", "HER2 to signaling pathways", "MMP9 to signaling pathways"],
  "relationships_to_explore": ["regulates", "activates", "inhibits", "interacts"],
  "query_strategy": "multiple_entities",
  "reasoning": "Question asks about multiple entities (HER2, MMP9, signaling pathways) and their interactions. Need separate queries for each relationship and then synthesis."
}}

If question is NOT about biomedical entities in the graph, return:
{{
  "entities": [],
  "aspects": [],
  "relationships_to_explore": [],
  "query_strategy": "no_graph_needed",
  "reasoning": "Question is about [patient info/general advice/etc], not specific biomedical entities"
}}
"""

    messages = [{'role': 'user', 'content': prompt}]
    models_to_try = _get_models_list(model_option)

    for model in models_to_try:
        try:
            response = client.chat.complete(
                model=model,
                messages=messages,
                temperature=config.ANALYSIS_TEMPERATURE
            )
            analysis_text = response.choices[0].message.content.strip()

            # Clean up the response to extract JSON
            analysis_text = _extract_json(analysis_text)

            # Parse JSON
            analysis = json.loads(analysis_text)
            return analysis

        except Exception as e:
            if model == models_to_try[-1]:
                # Return default analysis if all models fail
                return {
                    "entities": [],
                    "aspects": [],
                    "relationships_to_explore": [],
                    "query_strategy": "no_graph_needed",
                    "reasoning": "Failed to analyze question"
                }
            time.sleep(1)
            continue


def _build_conversation_context(conversation_history):
    # Build context string from recent conversation history
    if not conversation_history or len(conversation_history) <= 1:
        return ""

    recent_messages = conversation_history[-config.RECENT_MESSAGES_FOR_CONTEXT:]
    context = "Recent conversation context:\n"
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