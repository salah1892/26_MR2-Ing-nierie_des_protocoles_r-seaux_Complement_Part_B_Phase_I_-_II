from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from assistant.logging_utils import JsonlLogger
from assistant.rag_store import RagStore, Retrieved
from assistant.safety import check_safety
from assistant.text_utils import detect_language


@dataclass(frozen=True)
class AgentResponse:
    action: str
    answer: str
    language: str
    retrieved: list[Retrieved]
    eval_hooks: dict[str, Any]


def _format_context(retrieved: list[Retrieved]) -> str:
    parts = []
    for r in retrieved:
        parts.append(f"[source={r.source} chunk={r.chunk_id} score={r.score:.3f}]\n{r.text}")
    return "\n\n---\n\n".join(parts)


def _extractive_answer(user_text: str, retrieved: list[Retrieved]) -> str:
    if not retrieved:
        return "Je n'ai pas trouvé de document pertinent dans la base locale."
    # Simple “grounded” response: show steps + citations.
    top = retrieved[0]
    return (
        "Réponse (basée sur les documents locaux):\n\n"
        f"{top.text}\n\n"
        "Sources:\n"
        + "\n".join(f"- {r.source} (chunk {r.chunk_id})" for r in retrieved)
    )


def handle_query(
    *,
    user_text: str,
    rag: RagStore,
    logger: JsonlLogger,
    top_k: int = 4,
    allow_generation: bool = False,
) -> AgentResponse:
    """Agentic decision: safety -> tool selection -> retrieval -> response.

    Evaluation hooks are emitted as structured fields.
    """

    lang = detect_language(user_text)
    logger.log("Log_Interaction", user_text=user_text, language=lang)

    safety = check_safety(user_text)
    logger.log("Safety_Check", action=safety.action, reason=safety.reason)

    if safety.action == "refuse":
        answer = (
            "Je ne peux pas traiter des données personnelles/sensibles ici. "
            "Merci de retirer les identifiants (CIN, téléphone, email) ou contactez un agent." 
            f"Raison: {safety.reason}"
        )
        logger.log("Generate_Response", mode="refusal")
        return AgentResponse(
            action="refuse",
            answer=answer,
            language=lang,
            retrieved=[],
            eval_hooks={
                "after_Tool_Select": {"selected": "none", "reason": "safety_refusal"},
                "after_Generate_Response": {"type": "refusal"},
            },
        )

    if safety.action == "escalate":
        answer = (
            "Je vous redirige vers un agent humain pour ce cas. "
            "Veuillez fournir votre demande sans données sensibles, ou via le canal officiel."
        )
        logger.log("Generate_Response", mode="escalation")
        return AgentResponse(
            action="escalate",
            answer=answer,
            language=lang,
            retrieved=[],
            eval_hooks={
                "after_Tool_Select": {"selected": "human", "reason": "escalation_trigger"},
                "after_Generate_Response": {"type": "escalation"},
            },
        )

    # Tool selection: always retrieve first for procedural queries.
    logger.log("Tool_Select", selected="retrieve", top_k=top_k)

    retrieved = rag.retrieve(user_text, top_k=top_k)
    logger.log(
        "Tool_Result",
        selected="retrieve",
        retrieved_count=len(retrieved),
        retrieved_sources=[r.source for r in retrieved],
    )

    # In this prototype, generation is optional; we keep sovereignty by default.
    if not allow_generation:
        answer = _extractive_answer(user_text, retrieved)
        logger.log("Generate_Response", mode="extractive")
        return AgentResponse(
            action="retrieve_document",
            answer=answer,
            language=lang,
            retrieved=retrieved,
            eval_hooks={
                "after_Tool_Select": {"selected": "retrieve"},
                "after_Generate_Response": {"type": "extractive", "grounded": True},
            },
        )

    # Optional: connect a local LLM (e.g., Ollama). We keep the prompt grounded.
    from assistant.llm_ollama import generate_with_ollama

    context = _format_context(retrieved)
    prompt = (
        "You are a public administration assistant. Answer using ONLY the context. "
        "If the context is insufficient, say so.\n\n"
        f"User: {user_text}\n\nContext:\n{context}\n\nAnswer:"
    )
    llm = generate_with_ollama(prompt)
    logger.log("Generate_Response", mode="ollama", model=llm.model)

    return AgentResponse(
        action="summarize_procedure",
        answer=llm.text.strip() or _extractive_answer(user_text, retrieved),
        language=lang,
        retrieved=retrieved,
        eval_hooks={
            "after_Tool_Select": {"selected": "retrieve+generate", "model": llm.model},
            "after_Generate_Response": {"type": "llm", "grounded": True},
        },
    )
