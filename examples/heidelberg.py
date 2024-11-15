"""
Answer questions about a specific document set, in this case about information of Heidelberg in wikipedia
"""

from pydantic import BaseModel

from pharia_skill import ChatParams, ChatResponse, Csi, IndexPath, Message, skill

index = IndexPath("f13", "wikipedia-de", "luminous-base-asymmetric-64")


class Input(BaseModel):
    question: str


class Output(BaseModel):
    answer: str
    number_of_documents: int


@skill
def heidelberg(csi: Csi, input: Input) -> Output:
    "Answer questions about Heidelberg from Wikipedia"
    documents = csi.search(index, "Heidelberg", 3, 0.5)
    if not documents:
        return Output(answer="no relevant documents found", number_of_documents=0)
    context = "\n".join([doc.content for doc in documents])
    content = f"""Using the provided context documents below, answer the following question accurately and comprehensively. If the information is directly available in the context documents, cite it clearly. If not, use your knowledge to fill in the gaps while ensuring that the response is consistent with the given information. Do not fabricate facts or make assumptions beyond what the context or your knowledge base provides. Ensure that the response is structured, concise, and tailored to the specific question being asked.

Input: {context}

Question: {input.question}
"""
    message = Message.user(content)
    params = ChatParams(max_tokens=512)
    response: ChatResponse = csi.chat("pharia-1-llm-7b-control", [message], params)
    return Output(answer=response.message.content, number_of_documents=len(documents))
