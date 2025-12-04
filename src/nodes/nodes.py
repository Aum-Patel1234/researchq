from src.state.rag_state import RAGState


class RAGNodes:
    """ "Contains Node Funcs for RAG Workflow"""

    def __init__(self, retriever, llm) -> None:
        """
        Initialize RAG nodes with a retriever and an LLM.

        Parameters
        ----------
        retriever : BaseRetriever
            Retriever instance used to fetch semantically relevant documents.
        llm : Any
            Large language model interface with an `.invoke(prompt)` method.
        """
        self.retriever = retriever
        self.llm = llm

    def retrieve_docs(self, state: RAGState) -> RAGState:
        """
        Retrieve relevant documents based on the user's question.

        Parameters
        ----------
        state : RAGState
            Current state containing the input question.

        Returns
        -------
        RAGState
            Updated state containing the retrieved documents.
        """
        docs = self.retriever.invoke(state.question)
        return RAGState(question=state.question, retrieved_docs=docs)

    def generate_anser(self, state: RAGState) -> RAGState:
        """
        Generate an LLM-based answer using retrieved documents as context.

        Parameters
        ----------
        state : RAGState
            State containing the question and retrieved documents.

        Returns
        -------
        RAGState
            Updated state containing the generated answer.
        """
        context = "\n\n".join([doc.page_content for doc in state.retrieved_docs])

        prompt = f"""
        You are an advanced AI research assistant. Your job is to read the provided research-paper context
        and produce a long, detailed, structured, and deeply analytical answer.

        Your response MUST:

        - Be long and thorough (800+ words)
        - Include section headings and subsections
        - Explain background theory
        - Define all key terms
        - Walk through equations or methodology if applicable
        - Compare ideas with related work if context allows
        - Include limitations or assumptions
        - Provide examples or analogies
        - Summarize key takeaways clearly

        Use ONLY the information in the provided context. Do not hallucinate facts.
        If information is missing, explicitly state what is unknown.

        --------------------
        CONTEXT:
        {context}
        --------------------

        QUESTION:
        {state.question}

        --------------------
        Write your answer as a full-length explanatory article:
        """

        response = self.llm.invoke(prompt)

        return RAGState(
            question=state.question,
            retrieved_docs=state.retrieved_docs,
            answer=response.content,
        )
