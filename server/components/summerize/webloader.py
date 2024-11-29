from langchain_community.document_loaders import WebBaseLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
import dotenv
import os
from langchain_groq import ChatGroq

#os.environ["USER_AGENT"] = "web-agent"
dotenv.load_dotenv()

url = 'https://edition.cnn.com/2024/11/12/politics/trump-team-loyalists-analysis/index.html'
# 웹 문서 크롤링
loader = WebBaseLoader(url)

# 뉴스기사의 본문을 Chunk 단위로 쪼갬
text_splitter = CharacterTextSplitter(        
    separator="\n\n",
    chunk_size=3000,     # 쪼개는 글자수
    chunk_overlap=300,   # 오버랩 글자수
    length_function=len,
    is_separator_regex=False,
)



# 웹사이트 내용 크롤링 후 Chunk 단위로 분할
docs = WebBaseLoader(url).load_and_split(text_splitter)

# 각 Chunk 단위의 템플릿
template = '''다음의 내용을 한글로 요약해줘:
{text}
'''

# 전체 문서(혹은 전체 Chunk)에 대한 지시(instruct) 정의
combine_template = '''{text}

요약의 결과는 다음의 형식으로 작성해줘:칟
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

print(chain.invoke(docs))
        