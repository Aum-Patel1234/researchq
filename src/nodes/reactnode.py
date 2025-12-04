from typing import List, Optional
from src.state.rag_state import RAGState

from langchain_core.documents import Document
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent


class RAGNodes:
    """
    Node functions for a Research-Paper RAG workflow.

    This agent:
    - Retrieves relevant scientific documents
    - Uses ReAct reasoning steps to analyze context
    - Generates long, structured, high-quality research answers
    """

    def __init__(self, retriever, llm):
        """
        Parameters
        ----------
        retriever : BaseRetriever
            Vectorstore retriever for scientific PDFs.
        llm : Any
            Large language model used for reasoning and writing answers.
        """
        self.retriever = retriever
        self.llm = llm
        self._agent = None  # lazy init

    # 1. RETRIEVER NODE
    def retrieve_docs(self, state: RAGState) -> RAGState:
        """
        Retrieve top-k relevant research paper chunks.

        Parameters
        ----------
        state : RAGState
            State containing the user's research question.

        Returns
        -------
        RAGState
            Updated state with retrieved scientific passages.
        """
        docs = self.retriever.invoke(state.question)
        return RAGState(question=state.question, retrieved_docs=docs)

    # 2. RETRIEVER TOOL (for ReAct agent)
    def _build_tools(self) -> List[Tool]:
        """
        Build the retriever tool used inside the ReAct agent.

        The agent can call:
            - retriever(query)
        to fetch scientific passages on demand.
        """

        def retriever_tool_fn(query: str) -> str:
            docs: List[Document] = self.retriever.invoke(query)
            if not docs:
                return "No research documents found."

            merged = []
            for i, d in enumerate(docs[:8], start=1):
                meta = d.metadata or {}
                title = meta.get("title") or meta.get("source") or f"research_doc_{i}"
                page = meta.get("page") or "(unknown page)"
                merged.append(f"[{i}] Title: {title}\nPage: {page}\n\n{d.page_content}")

            return "\n\n".join(merged)

        # TODO: We can add more tools here
        retriever_tool = Tool(
            name="research_retriever",
            description="Retrieve scientific paragraphs relevant to the research question.",
            func=retriever_tool_fn,
        )

        return [retriever_tool]

    # 3. BUILD RESEARCH RAG AGENT (ReAct)
    def _build_agent(self):
        """
        Create a ReAct agent specialized for scientific reasoning.
        """

        tools = self._build_tools()

        system_prompt = (
            "You are a highly advanced AI research assistant trained to analyze scientific papers.\n"
            "Use ONLY the 'research_retriever' tool to fetch scientific passages.\n"
            "Your goal is to produce long, deeply structured, academically rigorous answers.\n"
            "When reasoning, think step-by-step, cite passages, and synthesize insights.\n"
            "Do NOT hallucinate—only use retrieved scientific context.\n"
            "Return only the final long-form answer, not your reasoning steps."
        )

        self._agent = create_react_agent(
            model=self.llm, tools=tools, prompt=system_prompt
        )

        return self._agent

    # 4. GENERATE ANSWER NODE
    def generate_answer(self, state: RAGState) -> RAGState:
        """
        Use the ReAct agent + retrieved scientific documents to generate
        a long, structured, research-grade answer.

        Parameters
        ----------
        state : RAGState
            State containing question + retrieved docs.

        Returns
        -------
        RAGState
            Updated state with the final answer.
        """

        if self._agent is None:
            self._agent = self._build_agent()

        result = self._agent.invoke(
            {"messages": [HumanMessage(content=state.question)]}
        )

        messages = result.get("messages", [])
        answer: Optional[str] = None
        if messages:
            answer_msg = messages[-1]
            answer = getattr(answer_msg, "content", None)

        return RAGState(
            question=state.question,
            retrieved_docs=state.retrieved_docs,
            answer=answer or "Could not generate a research answer.",
        )
