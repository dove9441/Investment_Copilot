from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate, ChatPromptTemplate
import dotenv

def getResponseBasedVectorSpace(question):
    dotenv.load_dotenv()
    embedding_model = HuggingFaceEmbeddings(
        model_name='jhgan/ko-sbert-nli',
        model_kwargs={'device':'cpu'},
        encode_kwargs={'normalize_embeddings':True},
    )
    vector_store = FAISS.load_local('./db/faiss', embedding_model, allow_dangerous_deserialization=True)


    template = '''Answer the question based as much as possible on the following context:
    {context}

    Question: {question}
    '''



    # LLM 객체 생성
    llm = ChatGroq(model="llama-3.1-8b-instant")
    retriever_from_llm = MultiQueryRetriever.from_llm(
        retriever=vector_store.as_retriever(
        ), llm=llm
    )
    prompt = ChatPromptTemplate.from_template(template)
    def format_docs(docs):
        return '\n\n'.join([d.page_content for d in docs])

    # Chain
    chain = (
        {'context': retriever_from_llm | format_docs, 'question': RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # Run
    response = chain.invoke(question)
    print(response)
    return response
    #print(response)