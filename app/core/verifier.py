from app.rag.retriever import retrieve_docs
from app.core.rules.ent_ars import evaluate_ent_ars


def verify_question(text: str, scope: str = "ent_ars") -> dict:
    # Simple orchestration example: retrieve docs then run rules
    docs = retrieve_docs(text, scope=scope)
    # For demo, pass empty symptoms to rules
    result = evaluate_ent_ars({})
    return {"docs": docs, "result": result}
