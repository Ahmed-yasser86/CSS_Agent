from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from Retrival_Pipline.Graph.state import GraphState
from Retrival_Pipline.Graph.const import GENERATE, GRADE_DOCUMENTS, RETRIEVE, WEBSEARCH
from Retrival_Pipline.Graph.Nodes.GradeDocument import grade_documents
from Retrival_Pipline.Graph.Nodes.Retrive import retrieve
from Retrival_Pipline.Graph.Nodes.GenerateNode import generate
from Retrival_Pipline.Graph.Nodes.web_search import websearch
from Retrival_Pipline.Graph.Chains.answer_grader import answer_grader
from Retrival_Pipline.Graph.Chains.hallucination_grader import hallucination_grader
from Retrival_Pipline.Graph.Chains.router import question_router

load_dotenv()



def route_question(state: GraphState) -> str:
    print("---ROUTE QUESTION---")
    question = state["question"]
    source: RouteQuery = question_router.invoke({"question": question})
    if source.datasource == WEBSEARCH:
        print("---ROUTE QUESTION TO WEB SEARCH---")
        return WEBSEARCH
    elif source.datasource == "vectorstore":
        print("---ROUTE QUESTION TO RAG---")
        return RETRIEVE



def evaluate_generated_answer(state: GraphState) -> str:
    print("---CHECK FOR HALLUCINATIONS---")

    user_question = state["question"]
    retrieved_documents = state["documents"]
    generated_answer = state["generation"]

    hallucination_result = hallucination_grader.invoke(
        {
            "documents": retrieved_documents,
            "generation": generated_answer,
        }
    )

    if is_grounded := hallucination_result.binary_score:
        print("---DECISION: ANSWER IS GROUNDED IN RETRIEVED DOCUMENTS---")
        print("---CHECK IF ANSWER ADDRESSES THE QUESTION---")

        answer_result = answer_grader.invoke(
            {
                "question": user_question,
                "generation": generated_answer,
            }
        )

        if answers_question := answer_result.binary_score:
            print("---DECISION: ANSWER ADDRESSES THE QUESTION---")
            return "useful"

        print("---DECISION: ANSWER DOES NOT ADDRESS THE QUESTION---")
        return "not useful"

    print("---DECISION: ANSWER IS NOT SUPPORTED BY THE RETRIEVED DOCUMENTS---")
    return "not supported"

def decide_to_generate(state):
    print("---ASSESS GRADED DOCUMENTS---")

    if state["web_search"]:
        print(
            "---DECISION: NOT ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, INCLUDE WEB SEARCH---"
        )
        return WEBSEARCH
    else:
        print("---DECISION: GENERATE---")
        return GENERATE





workflow = StateGraph(GraphState)
workflow.add_node(RETRIEVE, retrieve)
workflow.add_node(GRADE_DOCUMENTS, grade_documents)
workflow.add_node(GENERATE, generate)
workflow.add_node(WEBSEARCH, websearch)
workflow.add_edge(RETRIEVE, GRADE_DOCUMENTS)
workflow.add_conditional_edges(
    GRADE_DOCUMENTS,
    decide_to_generate,
    {
        WEBSEARCH: WEBSEARCH,
        GENERATE: GENERATE,
    },
)

workflow.set_conditional_entry_point(
    route_question,
    {
        WEBSEARCH: WEBSEARCH,
        RETRIEVE: RETRIEVE,
    },
)

workflow.add_edge(WEBSEARCH, GENERATE)

workflow.add_conditional_edges(
    GENERATE,
    evaluate_generated_answer,
    {
        "not supported": GENERATE,
        "useful": END,
        "not useful": WEBSEARCH,
    },
)

memory = MemorySaver()

#app = workflow.compile(checkpointer=memory, interrupt_after=["websearch"])

app = workflow.compile()


app.get_graph().draw_mermaid_png(output_file_path="graph.png")