# 필요한 라이브러리 임포트
import json
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate, ChatPromptTemplate
import dotenv
from langchain.chains import LLMChain
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
import os
from datetime import datetime
# 1. 데이터 로드 및 전처리

# JSON 데이터 로드 (예시를 위해 'news_articles.json' 파일을 사용한다고 가정합니다)

with open(f'./data/raw/news/collected_news_{datetime.now().strftime('%Y%m%d')}.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
dotenv.load_dotenv()
articles = data['articles']

def translate_text(text, source_language, target_language):
    template = f"Translate the following text from {source_language} to {target_language} preserving the original meaning:\n\n{text}\n\nTranslation:"
    llm = ChatGroq(model="llama-3.1-8b-instant")
    prompt = PromptTemplate(template=template, input_variables=['text'])
    chain = LLMChain(llm=llm, prompt=prompt, verbose=True)
    response = chain.invoke({'text':prompt})
    return response['text'].strip()

# 기사 내용 추출 및 전처리
documents = []
for idx, article in enumerate(articles):
    content = article.get('full_content')
    if content:
        doc = Document(
            page_content = translate_text(content, 'English', 'Korean'),
            metadata={
                'id': idx,
                'title' : article.get('title')
            }
        )
        documents.append(doc)
        
for doc in documents:
    print("===== Document =====")
    print("ID:", doc.metadata['id'])
    print("제목:", doc.metadata['title'])
    print("내용:")
    print(doc.page_content)
    print("====================\n")
# 2. 영어 임베딩 생성 및 벡터 스토어 구축
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = text_splitter.split_documents(documents)

# vector space 생성 

# HuggingFaceEmbeddings를 사용하여 임베딩 모델 로드
#embedding_model = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
embedding_model = HuggingFaceEmbeddings(
    model_name='jhgan/ko-sbert-nli',
    model_kwargs={'device':'cpu'},
    encode_kwargs={'normalize_embeddings':True},
)
vector_store = FAISS.from_documents(chunks,
                                    embedding = embedding_model,
                                    )
vector_store.save_local('./db/faiss')



llm = ChatGroq(model="llama-3.1-8b-instant")



# Prompt
template = '''Answer the question based only on the following context:
{context}

Question: {question}
'''


query = '주어진 기사들 중 경제, 정치와 관련있는 문서를 관련도 순대로 10개를 선정해서 각 문서를 한국어로 요약해줘.'

# LLM 객체 생성

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

# Test
response = chain.invoke('주어진 기사들 중 경제와 시장 상황, 투자에 관련된 기사 5개를 선정해서 각 기사를 한국어로 요약해줘.')
print(response)