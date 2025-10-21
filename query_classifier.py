import time
import config

def classify_question(client, question, model_option="Auto (tries multiple)"):
    # Classify question type: "GRAPH" for knowledge graph search or "DIRECT" for general answer
    prompt = f"""Analyze this user question and classify it:

Question: "{question}"

Classification rules:
- GRAPH: Question explicitly asks about specific scientific entities (gene names like BRCA1/TP53, protein names, drug names like Tamoxifen, specific pathways)
  Examples: "What is BRCA1?", "Tell me about the TP53 gene", "What drugs target HER2?", "Show me pathways related to PI3K"

- DIRECT: Everything else including:
  * Patient information (age, diagnosis, personal situations)
  * General questions (symptoms, risk factors, statistics, advice)
  * Conversational messages (greetings, thanks, follow-ups)
  * Questions about treatment options without naming specific entities
  Examples: "The patient is 55", "What are symptoms?", "Does age affect cancer risk?", "He has breast cancer"

RESPOND WITH ONLY: "GRAPH" or "DIRECT"
"""

    messages = [{'role': 'user', 'content': prompt}]
    models_to_try = _get_models_list(model_option)

    for model in models_to_try:
        try:
            response = client.chat.complete(
                model=model,
                messages=messages,
                temperature=config.CLASSIFICATION_TEMPERATURE
            )
            classification = response.choices[0].message.content.strip().upper()
            return "GRAPH" if "GRAPH" in classification else "DIRECT"
        except Exception:
            if model == models_to_try[-1]:
                return "DIRECT"  # Default to direct answer if all models fail
            time.sleep(1)
            continue

    return "DIRECT"

def _get_models_list(model_option):
    # Get model list based on selected option (auto fallback or single model)
    if model_option == "Auto (tries multiple)":
        return config.DEFAULT_MODELS
    else:
        return [model_option]