import time
import queue as q
import threading
import json
from fastapi import Request, FastAPI, Response
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from server.components.summerize.retrivial_from_vector_space import getResponseBasedVectorSpace
from server.components.responseHandlers import *
import requests
dotenv.load_dotenv()


##### 서버 생성 #####

app = FastAPI()

# Static files 경로 설정  예시 : (../data/visualizations 디렉토리를 /data/images 경로로 매핑)
static_path = Path(__file__).parent.parent #/Users/admin/Documents/OSS_TermProject/
app.mount("/data/images/visualizations", StaticFiles(directory=str(static_path)+'/data/visualizations'), name="visualizations_images")
app.mount("/data/images/market_data", StaticFiles(directory=str(static_path)+'/market_data'), name="market_data_images")
app.mount("/data/news", StaticFiles(directory=str(static_path)+'/data/raw/news'), name='collected_news')


@app.get("/")
async def root():
    return {"message": "kakaoTest"}

@app.post("/chat/")
async def chat(request: Request):
    kakaorequest = await request.json()
    # request에 URL이 포함되어있지 않아서 넣어줘야 한다
    scope = request.scope  # ASGI의 scope 객체
    scheme = scope.get("scheme", "http")
    host = scope["headers"][0][1].decode("utf-8")  # Host 헤더에서 호스트 정보 가져오기(base url넘기기)
    path = scope["path"]
    url = f"{scheme}://{host}{path}"
    kakaorequest["base_url"] = url


    #print(json.dumps(kakaorequest, indent=2))
    return mainChat(kakaorequest)



def post_in_background(url, data, headers):
    # 별도 스레드에서 POST 요청 처리
    r = requests.post(url, data=json.dumps(data), headers=headers)
    print("POST 요청 상태코드:", r.status_code)
    print("POST 응답 본문:", r.text)

def wait_and_post(response_queue, url, headers):
    # response_queue에 응답이 들어올 때까지 대기
    response = response_queue.get()  # 여기서 블로킹되어 응답을 기다림
    # 응답이 들어오면 post_in_background 실행
    post_in_background(url, response, headers)

def mainChat(kakaorequest):
    start_time = time.time()
    cwd = os.getcwd()
    filename = os.path.join(cwd, "botlog.txt")
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("")

    response_queue = q.Queue()
    request_respond = threading.Thread(target=AI_Response, args=(kakaorequest, response_queue, filename))
    request_respond.start()

    target_url = kakaorequest["userRequest"]["callbackUrl"]
    headers = {"Content-Type": "application/json"}

    delayedResponse = {
        "version": "2.0",
        "useCallback": "true",
        "data": {
            "text": "생각하고 있는 중이에요😘\n최대 1분 정도 소요될 거 같아요. 기다려 주실래요?!"
        }
    }

    immediateResponse = {
        "version": "2.0",
        "useCallback": "true",
        "data": {
        }
    }

    max_wait_time = 3.5
    response_data = None

    # 최대 3.5초 대기하며 queue 확인
    while (time.time() - start_time) < max_wait_time:
        if not response_queue.empty():
            # 큐가 차있다면 즉시 응답 반환
            response_data = response_queue.get()
            break
        time.sleep(0.1)  # 0.1초 간격으로 큐 상태 확인

    if response_data is not None:
        # 3.5초 이내 응답 도착 시 immediateResponse 반환
        client_response = Response(content=json.dumps(immediateResponse), media_type='application/json')
    else:
        # 3.5초 동안 대기했는데도 응답이 없다면 delayedResponse 반환
        client_response = Response(content=json.dumps(delayedResponse), media_type='application/json')

    # 반환 후에도 응답이 나중에 들어오면 post_in_background 호출
    def wait_and_post():
        if response_data is None:
            # 아직 응답을 못받은 경우 큐에 응답 들어올 때까지 대기
            final_response = response_queue.get()
        else:
            # 이미 response_data가 있는 경우 바로 사용
            final_response = response_data

        post_in_background(target_url, final_response, headers)

    threading.Thread(target=wait_and_post).start()

    return client_response




        