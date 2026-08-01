from typing import Any, Dict

from Retrival_Pipline.Graph.Chains.Generate import generate_chain
from Retrival_Pipline.Graph.state import GraphState


def generate(state: GraphState) -> Dict[str, Any]:
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    generation = generate_chain.invoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation}