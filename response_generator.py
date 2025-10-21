import time
import config
from query_executor import deduplicate_triplets, format_triplets_for_display

def synthesize_comprehensive_answer(client, question, analysis, query_results, conversation_history=None,
                                    model_option="Auto (tries multiple)"):

    if not query_results:
        return "I searched the knowledge graph but couldn't find information about the specific entities mentioned. Try asking about genes (like BRCA1, TP53), proteins (like HER2), or drugs (like Tamoxifen)."

    # Deduplicate and limit triplets
    triplets_list = deduplicate_triplets(query_results, config.MAX_TRIPLETS_FOR_SYNTHESIS)

    # Prepare concise results summary
    results_text = format_triplets_for_display(triplets_list)

    context = _build_conversation_context(conversation_history)

    prompt = f"""You are a biomedical expert. Synthesize a CONCISE, CLEAR answer from knowledge graph data.

{context}

Original question: "{question}"

Entities identified: {', '.join(analysis['entities'])}

{results_text}

CRITICAL REQUIREMENTS for your answer:
1. Be CONCISE - avoid repetition and redundancy
2. Focus on KEY findings only - don't list every relationship
3. Group similar relationships together (e.g., "X regulates multiple pathways including A, B, and C")
4. Provide a DIRECT answer to the question first
5. Add supporting details ONLY if they add meaningful value
6. Use 3-6 sentences for simple questions, more ONLY if truly complex
7. Avoid phrases like "According to the data" or "The results show" - just state the facts
8. Don't repeat entity names unnecessarily

AVOID:
- Listing every single triplet separately
- Repeating the same relationship type multiple times
- Over-explaining simple connections
- Unnecessary introductions or conclusions
- Redundant phrases

Structure for complex answers:
- Opening: Direct answer (1 sentence)
- Body: Key mechanisms/relationships (2-4 sentences)  
- Closing: Clinical relevance if applicable (1 sentence)

Respond in the same language as the question.

Your concise, focused answer:"""

    messages = [{'role': 'user', 'content': prompt}]
    models_to_try = _get_models_list(model_option)

    for model in models_to_try:
        try:
            response = client.chat.complete(
                model=model,
                messages=messages,
                temperature=config.SYNTHESIS_TEMPERATURE
            )
            answer = response.choices[0].message.content.strip()

            # Post-processing: Remove common redundant patterns
            answer = _clean_answer(answer)

            return answer
        except Exception as e:
            if model == models_to_try[-1]:
                return "Found relevant information but had trouble formulating the response. Please try rephrasing your question."
            time.sleep(1)
            continue


def generate_direct_answer(client, question, conversation_history=None, model_option="Auto (tries multiple)"):
    # Generate direct answer for patient info, general questions, or conversational messages (no graph search)
    context = _build_extended_conversation_context(conversation_history)

    prompt = f"""You are a knowledgeable and empathetic medical assistant specialized in breast cancer.

{context}

User's message: {question}

Instructions:
- If it's just patient information (age, diagnosis status): Acknowledge it professionally and ask how you can help
- If it's about risk factors, symptoms, treatment options: Provide clear medical information
- If it's a personal situation: Be supportive and recommend consulting healthcare professionals
- If it's a greeting or thanks: Respond naturally and warmly
- Keep responses concise (2-4 sentences) and professional
- Respond in the same language as the user

Your response:"""

    messages = [{'role': 'user', 'content': prompt}]
    models_to_try = _get_models_list(model_option)

    for model in models_to_try:
        try:
            response = client.chat.complete(
                model=model,
                messages=messages,
                temperature=config.DIRECT_ANSWER_TEMPERATURE
            )
            return response.choices[0].message.content
        except Exception as e:
            if model == models_to_try[-1]:
                return "I apologize, but I'm having trouble processing your question right now. Please try again in a moment."
            time.sleep(1)
            continue


def _build_conversation_context(conversation_history):
    # Build short context string from recent conversation history
    if not conversation_history or len(conversation_history) <= 1:
        return ""

    recent_messages = conversation_history[-config.RECENT_MESSAGES_FOR_CONTEXT:]
    context = "\n\nPrevious conversation:\n"
    for msg in recent_messages:
        content = msg['content'][:200]
        context += f"{msg['role'].title()}: {content}\n"

    return context


def _build_extended_conversation_context(conversation_history):
    # Build extended context string with more conversation history
    if not conversation_history or len(conversation_history) <= 1:
        return ""

    recent_messages = conversation_history[-config.MAX_CONVERSATION_HISTORY:]
    context = "\n\nConversation history:\n"
    for msg in recent_messages:
        content = msg['content'][:300]
        context += f"{msg['role'].title()}: {content}\n"

    return context


def _clean_answer(answer):
    # Remove redundant phrases like "According to the data" from answer
    redundant_phrases = [
        "According to the knowledge graph, ",
        "The data shows that ",
        "Based on the relationships, ",
        "The results indicate that ",
        "According to the data, ",
        "The information shows that "
    ]

    for phrase in redundant_phrases:
        answer = answer.replace(phrase, "")

    return answer


def _get_models_list(model_option):
    # Return list of models to try based on selected option
    if model_option == "Auto (tries multiple)":
        return config.DEFAULT_MODELS
    else:
        return [model_option]