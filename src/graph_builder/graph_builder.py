from src.nodes.nodes import RAGNodes
from src.state.rag_state import RAGState
from langgraph.graph import StateGraph, END


class GraphBuilder:
    """
    Build and manage a LangGraph workflow for a Retrieval-Augmented Generation (RAG) pipeline.

    This class:
      - Creates the computation graph
      - Registers the retriever and LLM responder nodes
      - Links nodes using directed edges
      - Provides a simple `run()` method to execute the workflow
    """

    def __init__(self, retriever, llm) -> None:
        """
        Initialize the graph builder.

        Parameters
        ----------
        retriever : BaseRetriever
            A retriever instance that provides semantic document retrieval.
        llm : Any
            Large language model interface with a callable generation method.
        """
        self.nodes = RAGNodes(retriever, llm)
        self.graph = None

    def build(self):
        """
        Return compiled Graph instance

        Workflow steps:
        ----------------
        retriever → responder → END
        """
        builder = StateGraph(RAGState)

        # nodes
        builder.add_node("retriever", self.nodes.retrieve_docs)
        builder.add_node("responder", self.nodes.generate_anser)

        builder.set_entry_point("retriever")

        # add edges
        builder.add_edge("retriever", "responder")
        builder.add_edge("responder", END)

        self.graph = builder.compile()
        return self.graph

    def run(self, question: str) -> dict:
        """
        Execute the RAG workflow for a given question.

        Parameters
        ----------
        question : str
            The user input question to be processed.

        Returns
        -------
        dict
            The final state output produced by the graph execution.
        """
        if self.graph is None:
            self.graph = self.build()

        initial_state = RAGState(question=question)
        return self.graph.invoke(initial_state)
