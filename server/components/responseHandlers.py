from server.components.summerize.retrivial_from_vector_space import getResponseBasedVectorSpace
import time
from langchain_community.document_loaders import WebBaseLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
import dotenv
import os
from langchain_groq import ChatGroq
from langchain.docstore.document import Document # 텍스트를 document 객체로 변환
from fastapi import Request
from langchain.chains import LLMChain
import pandas as pd
from datetime import date, datetime
import json



# 텍스트 파일 초기화
def dbReset(filename):
    with open(filename, 'w') as f:
        f.write("")


# 메시지 응답 포맷
def textResponseFormat(bot_response):
    #print('------------BOT_RESONSE-------------')
    #print(bot_response)
    response = {"version":"2.0", "template":{"outputs":[{"simpleText":{"text":bot_response}}], "quickReplies":[]}}
    return response

# 사진 응답 포맷
def imageResponseFormat(bot_response, prompt):
    output_text = prompt + "내용에 관한 이미지입니다"
    response = {"version":"2.0", "template":{"outputs":[{"simpleImage":{"imageUrl":bot_response, "altText":output_text}}], "quickReplies":[]}}
    return response



# 메시지 응답 핸들러
def AI_Response(request, response_queue, filename):
    print(json.dumps(request, indent=2))
    # 사용자가 버튼을 클릭하여 답변 완성 여부를 다시 봤을 시
    if '생각 다 끝났나요?' in request["userRequest"]["utterance"]:
        # 텍스트 파일 열기
        with open(filename) as f:
            last_update = f.read()
        # 텍스트 파일 내 저장된 정보가 있을 경우
        if len(last_update.split()) > 1:
            kind, bot_res, prompt = last_update.split()[0], last_update.split()[1], last_update.split()[2]
            response_queue.put(textResponseFormat(last_update))
            dbReset(filename)

    # 오늘의 정보 요청

    elif '/get C' in request["userRequest"]["utterance"]: 
        dbReset(filename)
        prompt = request["userRequest"]["utterance"].replace("/get", "")
        response_queue.put(getCorrelationMatrix(request))

    elif '/v' in request["userRequest"]["utterance"]: 
        dbReset(filename)
        prompt = request["userRequest"]["utterance"].replace("/v", "")
        bot_res = getResponseBasedVectorSpace(prompt)
        response_queue.put(textResponseFormat(bot_res))
        save_log = str(bot_res)
        with open(filename, 'w') as f:
            f.write(save_log)

    elif '오늘의 뉴스' == request["userRequest"]["utterance"]: 
        dbReset(filename)
        bot_res = getResponseBasedVectorSpace('주어진 기사들 중 경제와 시장 상황, 투자, 정치에 관련된 기사 10개를 선정해서 각 기사를 한국어로 요약해줘.')
        response_queue.put(textResponseFormat(bot_res))
        save_log = str(bot_res)
        with open(filename, 'w') as f:
            f.write(save_log)

    elif 'Fear & Greed' in request["userRequest"]["utterance"]: 
        dbReset(filename)
        response_queue.put(getFearandGreed(request))

    elif 'Dashboard' == request["userRequest"]["utterance"]: 
        dbReset(filename)
        response_queue.put(getDashboard(request))

    elif '주요 종목' == request["userRequest"]["utterance"]: 
        dbReset(filename)
        response_queue.put(getIndex(request))
    
    elif '/s' in request["userRequest"]["utterance"]:
        dbReset(filename)
        prompt = request["userRequest"]["utterance"].replace("/s", "")
        bot_res = getSearchResponse_LLAMA(prompt)
        response_queue.put(textResponseFormat(bot_res))
        save_log = str(bot_res)
        with open(filename, 'w') as f:
            f.write(save_log)
    # 일반 LLM 답변을 요청한 경우
    #elif '/ask' in request["userRequest"]["utterance"]:
    # 기본값을 LLAMA 답변으로 설정
    else:
        #print(json.dumps(request, indent=2))
        dbReset(filename)
        prompt = request["userRequest"]["utterance"]#.replace("/ask", "")
        bot_res = getTextFromLLAMA(prompt)#getTextFromLLAMA(prompt)
        response_queue.put(textResponseFormat(bot_res))

        save_log = "ask" + " " + str(bot_res) + " " + str(prompt)
        with open(filename, 'w') as f:
            f.write(save_log)
    # 아무 답변 요청이 없는 채팅일 경우
    # else:
    #     # 기본 response 값
    #     defaultText = "아무 답변 요청이 없는 메시지입니다."
    #     base_response = {
    #                         "version": "2.0",
    #                         "template": {
    #                             "outputs": [
    #                             {
    #                                 "simpleText": {
    #                                     "text": "default"
    #                                 }
    #                             }
    #                             ]
    #                         }
    #                         }
    #     response_queue.put(textResponseFormat(defaultText))


def getTextFromLLAMA(prompt):
    llm = ChatGroq(model="llama-3.1-8b-instant")#llama-3.1-70b-versatile / llama-3.1-8b-instant
    combine_prompt = PromptTemplate(input_variables=['text'], template="You are an participatnt in 1:1 dialogue. Response about quesition. : {text}.")
    chain = LLMChain(llm=llm, prompt=combine_prompt, verbose=True)
    response = chain.invoke({'text':prompt})
    return response['text']



def getSummeryFromLLM(text):
    # 각 Chunk 단위의 템플릿
    template = '''다음의 내용을 한글로 요약해줘:
    {text}
    '''
    # 전체 문서(혹은 전체 Chunk)에 대한 지시(instruct) 정의
    combine_template = '''{text}

    요약의 결과는 다음의 형식으로 작성해줘.
    제목: 기사 제목
    요약: 3줄로 요약된 내용
    세부내용: 주요내용을 작성
    '''
    # 템플릿 생성
    prompt = PromptTemplate(template=template, input_variables=['text'])
    combine_prompt = PromptTemplate(template=combine_template, input_variables=['text'])

    # LLM 객체 생성
    llm = ChatGroq(model="llama-3.1-8b-instant")#llama-3.1-70b-versatile")
    #llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo-16k')

    # 요약을 도와주는 load_summarize_chain
    chain = load_summarize_chain(llm,  map_prompt=prompt, combine_prompt=combine_prompt, chain_type="map_reduce", verbose=True)
    text_docs = Document(page_content=text)
    summerized_msg = chain.invoke([text_docs])
    return summerized_msg


################################# WEBSEARCH RAG TEST ######################
import streamlit as st
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from duckduckgo_search import DDGS
import re

# performs DuckDuckGo search, urls are extracted and status checked
# 
def ddg_search(query):
    results = DDGS().text(query, max_results=5, backend='api', timelimit='w')
    urls = []
    for result in results:
        url = result['href']
        urls.append(url)

    docs = get_page(urls)

    content = []
    for doc in docs:
        page_text = re.sub("\n\n+", "\n", doc.page_content)
        text = truncate(page_text)
        content.append(text)
    return content

# retrieves pages and extracts text by tag
def get_page(urls):
    loader = AsyncChromiumLoader(urls)
    html = loader.load()

    bs_transformer = BeautifulSoupTransformer()
    docs_transformed = bs_transformer.transform_documents(html, tags_to_extract=["p"], remove_unwanted_tags=["a"])

    return docs_transformed

# helper function to reduce the amount of text
def truncate(text):
    words = text.split()
    truncated = " ".join(words[:400])

    return truncated

def getSearchResponse_LLAMA(query):
    search_results = ddg_search(query)
    if not search_results:
        return "No search results found or an error occurred."

    # LLM initialization
    llm = ChatGroq(model="llama-3.1-8b-instant")  # Ensure this model exists and is configured

    # Prompt template
    combine_prompt = PromptTemplate(
        input_variables=['text', 'search_results'],
        template="You are a participant in a 1:1 dialogue. Respond to the question using the search results. "
                 "Question: {text}\n"
                 "Search Results: {search_results}\n"
                 "Answer:"
    )

    # Chain setup
    chain = LLMChain(llm=llm, prompt=combine_prompt, verbose=True)
    try:
        response = chain.invoke({'text': query, 'search_results': "\n".join(search_results)})
        return response['text']
    except Exception as e:
        print(f"Error during LLM invocation: {e}")
        return "An error occurred while generating the response."


# 정보 보내주는 함수들
def getFearandGreed(request: Request):
    # CSV 파일 경로
    file_path = "/Users/admin/Documents/OSS_TermProject/data/raw/fear_greed_index.csv"
    df = pd.read_csv(file_path)

    # 마지막 행의 마지막 열 값 읽기
    score = round(float(df.iloc[-1, -1]))
    base_url = request["base_url"]
    fear_greed_image_url = f"{base_url.replace("chat/", "")}data/images/market_data/half_circle_gauge_{datetime.now().strftime("%Y%m%d")}.png" 
    cor_image_url = f"{base_url.replace("chat/", "")}data/images/market_data/correlation_matrix_20241208_022323.png"
    # 오늘 날짜 가져오기
    today = date.today()
    formatted_date = today.strftime("%Y-%m-%d")
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
            {
                "basicCard": {
                "title": "Fear & Greed Index",
                "description": "현재 시장의 감정적 흐름에 대해 나타냅니다. {today}, 시장의 Fear & Greed index 지수는 {score}입니다.",
                "thumbnail": {
                    "imageUrl": fear_greed_image_url
                }
                }
            },
            ]
        }
        }
    # description 필드의 문자열을 동적으로 업데이트
    response["template"]["outputs"][0]["basicCard"]["description"] = \
    response["template"]["outputs"][0]["basicCard"]["description"].format(today=formatted_date, score=score)
    return response

def getDashboard(request : Request):
    base_url = request["base_url"]
    dashboard_image_url = f"{base_url.replace("chat/", "")}data/images/market_data/dashboard_{datetime.now().strftime("%Y%m%d")}.png"
    index_image_url = f"{base_url.replace("chat/", "")}data/images/market_data/table_주요지수_{datetime.now().strftime("%Y%m%d")}.png"
    response = {
    "version": "2.0",
    "template": {
        "outputs": [
        {
        "simpleImage": { "imageUrl": dashboard_image_url }
        },
        {
        "simpleImage": { "imageUrl": index_image_url }
        }

    ]
    }
    }
    return response

def getIndex(request : Request):
    base_url = request["base_url"]
    index_url_1 = f"{base_url.replace("chat/", "")}data/images/market_data/table_기술주_{datetime.now().strftime("%Y%m%d")}.png"
    index_url_2 = f"{base_url.replace("chat/", "")}data/images/market_data/table_원자재_{datetime.now().strftime("%Y%m%d")}.png"
    index_url_3 = f"{base_url.replace("chat/", "")}data/images/market_data/table_국채수익률_{datetime.now().strftime("%Y%m%d")}.png"
    response = {
    "version": "2.0",
    "template": {
        "outputs": [
        {
        "simpleImage": { "imageUrl": index_url_1 }
        },
        {
        "simpleImage": { "imageUrl": index_url_2 }
        },
        {
        "simpleImage": { "imageUrl": index_url_3 }
        }

    ]
    }
    }
    return response

def getCorrelationMatrix(request : Request):
    # 클라이언트 요청의 호스트 URL 가져오기
    base_url = request["base_url"]
    image_url = f"{base_url.replace("chat/", "")}data/images/market_data/correlation_matrix_20241128_163021.png"
    # 오늘 날짜 가져오기
    today = date.today()
    formatted_date = today.strftime("%Y-%m-%d")
    r = {
    "version": "2.0",
    "template": {
        "outputs": [
            {
                "simpleImage": {
                    "imageUrl": image_url,
                    "altText": "alt"
                },
            },
            {
                "simpleText": {
                    "text": "Stock Price & Index Correlation Matrix between famous U.S companies\n미국 주요 주가 지수와 대표 기업들의 주가의 상관관계에 관한 지표입니다. 1에 가까울수록 연관성이 높습니다."
                }
            }
            
        ]
    }
    }
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
            {
                "basicCard": {
                "title": "Stock Price & Index Correlation Matrix between famous U.S companies ",
                "description": "미국 주요 주가 지수와 대표 기업들의 주가의 상관관계에 관한 지표입니다. 1에 가까울수록 연관성이 높습니다.",
                "thumbnail": {
                    "imageUrl": image_url
                }
                }
            }
            ]
        }
        }
    return r