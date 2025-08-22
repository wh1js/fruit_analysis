import datetime
from fastapi import FastAPI, UploadFile, Form, HTTPException, File, Depends
from fastapi.responses import FileResponse
import os
import time
import uvicorn
import aiomqtt
from contextlib import asynccontextmanager
import asyncio
import json
import mimetypes
import aiohttp
from networkx.algorithms.approximation.distance_measures import diameter

from baidu_cnn_lstm import baidu_cnnlstm
from baidu_yolo import baidu_ppyolos
from baidu_seg import baidu_seg_two_images
from render import render,build_loquat_json,process_json_data,fetch_env_json,get_fruit_quality
from big_model_ai_analysis import big_model_ai_analysis

# 定义生命周期处理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时连接 MQTT 客户端
    async with aiomqtt.Client(hostname="localhost", port=1883) as client:
        await client.subscribe("send-sugar")
        app.state.mqtt_client = client
        listener_task = asyncio.create_task(mqtt_listener(client))
        yield  # 应用程序运行期间保持运行
        listener_task.cancel()  # 应用程序关闭时取消任务


from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有域名跨域访问
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)



# 用于保存当前序列的文件夹路径
current_folder = "upload_images"
image_count = 0

file_lock = False

#regression_model = RegressionModel()


# 定义依赖函数以获取 MQTT 客户端
def get_mqtt_client():
    return app.state.mqtt_client


@app.post("/upload")
async def upload(type: str = Form(...), file: UploadFile = File(None)):
    global current_folder, image_count
    if type == "start":
        # 当接收到 start 请求时，创建以当前时间戳命名的文件夹
        timestamp = int(time.time())
        folder_name = f"{current_folder}/{timestamp}"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            print("created folder")
        current_folder = folder_name
        return {"status": "start received"}
    elif type == "image" and file:
        # 当接收到 image 请求时，保存图片到当前文件夹
        if current_folder == "upload_images":
            raise HTTPException(status_code=400, detail="No sequence started")
        if file is None:
            raise HTTPException(status_code=400, detail="No file provided")
        # 使用毫秒时间戳生成唯一文件名
        filename = f"image_{image_count}.jpg"
        file_path = os.path.join(current_folder, filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())  # 异步读取文件内容并写入
        image_count += 1
        return {"status": "image received"}
    elif type == "end":
        # 当接收到 end 请求时，结束当前序列
        if current_folder == "upload_images":
            raise HTTPException(status_code=400, detail="No sequence started")
        current_folder = "upload_images"
        image_count = 0
        return {"status": "end received"}
    else:
        raise HTTPException(status_code=400, detail="Invalid type")


@app.post("/measure-fruit/{count}")
async def control_light(count: str, mqtt_client: aiomqtt.Client = Depends(get_mqtt_client)):
    await mqtt_client.publish("measure_once", count)
    return {"message": "Light control command sent"}

@app.post("/measure-fruit-analyze")
async def measure_fruit(mqtt_client: aiomqtt.Client = Depends(get_mqtt_client)):
    global file_lock
    await mqtt_client.publish("measure_once", "1")
    file_lock = False
    while file_lock is False:
        await asyncio.sleep(0.5)
    dir_name_list = os.listdir(current_folder)
    dir_name = max(dir_name_list)
    ph, water, sugar = await asyncio.to_thread(baidu_cnnlstm, f"{current_folder}/{dir_name}/specturm.txt")
    return ph, water, sugar

@app.post("/measure-fruit-analyze-report")
async def measure_fruit_report(mqtt_client: aiomqtt.Client = Depends(get_mqtt_client)):

    global file_lock
    await mqtt_client.publish("measure_once", "1")
    file_lock = False
    while file_lock is False:
        await asyncio.sleep(0.5)
    dir_name_list = os.listdir(current_folder)
    dir_name = max(dir_name_list)
    file_folder = f"{current_folder}/{dir_name}"
    print("111", file_folder)

    task_regression = asyncio.create_task(asyncio.to_thread(baidu_cnnlstm, f"{current_folder}/{dir_name}/specturm.txt"))
    task_yolo = asyncio.create_task(asyncio.to_thread(baidu_ppyolos, f"{current_folder}/{dir_name}/image_0.jpg",
                                                      f"{current_folder}/{dir_name}/image_2.jpg"))
    task_seg = asyncio.create_task(asyncio.to_thread(baidu_seg_two_images, f"{current_folder}/{dir_name}/image_0.jpg",
                                                     f"{current_folder}/{dir_name}/image_2.jpg"))

    ph, water, sugar = await task_regression
    black, guo_len, yolo_save_path = await task_yolo
    damage_s_all, seg_output_image_path = await task_seg

    env_json = fetch_env_json()
    input_json = build_loquat_json(ph, water, sugar, damage_s_all, black, guo_len, env_json)
    input_dict = process_json_data(input_json)
    #global show_text
    #show_text = f"枇杷的糖度为{result['sugar']}白利，{sugar_grade}，PH值为{result['ph']}，水分为百分之{result['water']}，黑点数{black_point}个，擦伤面积{broken_area}平方厘米，果径{diameter}厘米，品质为{diameter_grade}。"
    #print(show_text)

    sugar_grade, diameter_grade = get_fruit_quality(sugar, guo_len)
    await mqtt_client.publish("sugar_server/detect_results", json.dumps(result.update(
        {"bp": black, "broken_area": damage_s_all, "diameter": guo_len, "diameter_grade": diameter_grade, "sugar_grade": sugar_grade})))

    text, quality, solving = await asyncio.to_thread(big_model_ai_analysis, input_dict)

    doc_path = await asyncio.to_thread(render, input_dict, "枇杷品质分析：{}\n解决方案：{}".format(text, solving),
                                       quality, f"{current_folder}/{dir_name}/specturm.txt", yolo_save_path,
                                       seg_output_image_path)


    mime_type, _ = mimetypes.guess_type(doc_path)
    print(doc_path, mime_type)
    if doc_path.endswith(".doc"):
        mime_type = "application/msword"
    elif doc_path.endswith(".docx"):
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        mime_type = mime_type or "application/octet-stream"  # 回退到通用类型

        # 返回文件下载响应
    return FileResponse(
        path=doc_path,
        media_type=mime_type,
        filename=f"水果检测结果{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}报告.docx",
    )



async def mqtt_listener(client: aiomqtt.Client):
    global current_folder, file_lock
    async for message in client.messages:
        payload = message.payload.decode("utf-8")
        if message.topic.matches("send-sugar"):
            dir_name_list = os.listdir("upload_images")
            dir_name = max(dir_name_list)
            try:
                print(dir_name)
                payload = json.loads(payload)
                with open(f"{current_folder}/{dir_name}/specturm.txt", "a", encoding="UTF8") as f:
                    f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            except Exception as e:
                print("Json Write Error", e)
        file_lock = True

# 运行服务器
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6200)


