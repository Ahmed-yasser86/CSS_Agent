from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from StateGraph import GraphState
from Nodes.IdentityResearchNode import make_identity_research

load_dotenv()

# Constants
IDENTITY_RESEARCH = "identity_research"
HUMAN_REVIEW = "human_review"
MAX_ITERATIONS = 3


async def human_review_node(state: GraphState) -> dict:
    """
    Human review node: Shows report and collects user decision.
    """
    print("---HUMAN REVIEW OF IDENTITY REPORT---")
    identity_data = state.get("identity_data", {})
    report = identity_data.get("report", "No report generated.")
    
    print("\n" + "="*30 + " IDENTITY REPORT " + "="*30)
    print(report)
    print("="*75)
    
    # Get iteration count from identity_data or default
    iteration = identity_data.get("research_iteration", 1)
    print(f"\n📊 Research Iteration: {iteration}/{MAX_ITERATIONS}")
    
    choice = input("\nIs the report accurate and does it match the requested person? (y/n): ").strip().lower()
    
    if choice == 'y':
        print("---DECISION: REPORT APPROVED BY USER---")
        return {
            "identity_data": {
                **identity_data,
                "approved": True,
                "needs_reprocessing": False,
                "research_iteration": iteration + 1
            }
        }
    else:
        feedback = input("Please provide additional details to update the search: ").strip()
        print("---DECISION: USER REQUESTED RE-SEARCH WITH FEEDBACK---")
        
        # Check max iterations
        if iteration >= MAX_ITERATIONS:
            print("⚠️ Maximum research iterations reached. Ending process.")
            return {
                "identity_data": {
                    **identity_data,
                    "approved": False,
                    "needs_reprocessing": False,  # Stop the loop
                    "feedback_notes": feedback,
                    "research_iteration": iteration + 1
                }
            }
        
        # Update chain_input with feedback
        chain_input = state.get("chain_input", {})
        
        return {
            "chain_input": {
                **chain_input,
                "query": f"{chain_input.get('query', '')} {feedback}"  # Add feedback to query
            },
            "identity_data": {
                **identity_data,
                "approved": False,
                "needs_reprocessing": True,  # Enable reprocessing
                "feedback_notes": feedback,
                "research_iteration": iteration + 1
            }
        }


def decide_to_reprocess(state: GraphState) -> str:
    """
    Decision function: Checks needs_reprocessing flag.
    """
    print("---ASSESS IDENTITY REPROCESSING FLAG---")
    
    identity_data = state.get("identity_data", {})
    needs_retry = identity_data.get("needs_reprocessing", False)
    
    if needs_retry:
        print("---DECISION: NEEDS RE-PROCESSING (TRUE) -> RETRY RESEARCH---")
        return IDENTITY_RESEARCH
    else:
        print("---DECISION: APPROVED OR NO RE-PROCESSING -> END---")
        return END


# Build workflow
workflow = StateGraph(GraphState)

# Add nodes
workflow.add_node(IDENTITY_RESEARCH, make_identity_research)
workflow.add_node(HUMAN_REVIEW, human_review_node)

# Set entry point
workflow.set_entry_point(IDENTITY_RESEARCH)

# Add edges
workflow.add_edge(IDENTITY_RESEARCH, HUMAN_REVIEW)

# Add conditional edges
workflow.add_conditional_edges(
    HUMAN_REVIEW,
    decide_to_reprocess,
    {
        IDENTITY_RESEARCH: IDENTITY_RESEARCH,
        END: END
    }
)

# Compile with memory
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# Save graph visualization
try:
    app.get_graph().draw_mermaid_png(output_file_path="identity_graph.png")
except Exception as e:
    print(f"Could not save graph visualization: {e}")


# Test run
if __name__ == "__main__":
    import asyncio
    
    async def run_test():
        initial_state = {
            "chain_input": {
                "query": "mostafa el adawy the egyptian salafai"
            },
            "identity_data": {
                "research_iteration": 1
            }
        }
        
        print("🚀 Starting Human-in-the-Loop Identity Graph...")
        
        config = {"configurable": {"thread_id": "identity_research_test"}}
        
        try:
            final_state = await app.ainvoke(initial_state, config=config)
            print("\n🏁 Graph Execution Completed Successfully!")
            
            identity_data = final_state.get("identity_data", {})
            print(f"Final approval status: {identity_data.get('approved', False)}")
            print(f"Total iterations: {identity_data.get('research_iteration', 1) - 1}")
            
        except Exception as e:
            print(f"Error occurred: {e}")
    
    asyncio.run(run_test())