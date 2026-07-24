from typing import Any, Dict
from state import GraphState
from Ingestion_Pipline.RagRetrival import retive_query
from dotenv import load_dotenv
from Ingestion_Pipline.RagRetrival import retive_query
load_dotenv()
from Ingestion_Pipline.config.settings import ChatModelSettings, DEFAULT_COLLECTION_NAME, EmbeddingSettings
from Ingestion_Pipline.infra.embeddings import build_embeddings
from Generate import generate_chain  
from Ingestion_Pipline.RagRetrival import  retive_query

embeddings = build_embeddings(EmbeddingSettings())

async def retrieve(state: GraphState) -> Dict[str, Any]:
    print("---RETRIEVE---")
    question = state["question"]

    documents =  await retive_query(
        embeddings,
        "MyAgenticRagApp",
        question
    )

    return {"documents": documents, "question": question}