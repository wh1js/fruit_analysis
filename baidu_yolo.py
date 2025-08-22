# 以下仅为基础调用示例
# 请前往 https://paddlepaddle.github.io/PaddleX/3.0/pipeline_usage/tutorials/cv_pipelines/object_detection.html#3 了解更多功能

import base64
import requests
import os

def baidu_ppyolos(image_path1, image_path2):
    API_URL = 'xxxxxxxxxxxxxx'
   
    # 请前往 https://aistudio.baidu.com/index/accessToken 查看"访问令牌"并替换
    TOKEN = "xxxxxxxxxxxxxxxxxxxxx"

    # Determine the predict folder number
    base_dir = "model_runs_results/baidu_yolo_runs"
    predict_num = 1
    while True:
        predict_dir = f"predict{predict_num}"
        if not os.path.exists(os.path.join(base_dir, predict_dir)):
            os.makedirs(os.path.join(base_dir, predict_dir), exist_ok=True)
            break
        predict_num += 1
        #yolo_save_path="model_runs_sults/baidu_yolo_runs/predict{}".format(predict_num)
        #print("YOLO : YOLO RESULT HAS BEEN GET TO {}".format(yolo_save_path) )
    blackpoint=0
    guo_len_list=[]
    output_image_path_list=[]
    for image_path in [image_path1, image_path2]:
        # 对本地图像进行Base64编码
        with open(image_path, "rb") as file:
            image_bytes = file.read()
            image_data = base64.b64encode(image_bytes).decode("ascii")

        # 设置标头
        headers = {
            "Authorization": f"token {TOKEN}",
            "Content-Type": "application/json"
        }

        # 设置请求体
        payload = {"image": image_data}  # Base64编码的文件内容或者图像URL

        # 调用API
        response = requests.post(API_URL, json=payload, headers=headers)

        # 处理接口返回数据
        assert response.status_code == 200
        result = response.json()["result"]
        output_image_path = os.path.join(base_dir, predict_dir, f"out{int([image_path1, image_path2].index(image_path))+1}.jpg")
        output_image_path_list.append(output_image_path)
        with open(output_image_path, "wb") as file:
            file.write(base64.b64decode(result["image"]))


        # 分析检测结果

        detected_objects = result["detectedObjects"]
        for i in detected_objects:
            if i["categoryName"]=='class_1':
                blackpoint+=1
            try:
                guo_len_list.append(i["bbox"][2]-i["bbox"][0])

            except:
                print("THE BBOX NAMED class0 IS NOT FOUND")
    try:
        scaling = 0.015
        guo_len = max(guo_len_list) * scaling
    except:
        print("未测得枇杷")
        guo_len=0
    print("果径:{} \n 黑点数:{}".format(guo_len,blackpoint))

    return blackpoint,guo_len,output_image_path_list


if __name__ == '__main__':
    image1 = "upload_images/1754984861/image_0.jpg"
    image2 = "upload_images/1754984861/image_2.jpg"
    black,guo_len,yolo_save_path=baidu_ppyolos(image1,image2)

    print("yolo_output_image_path:",yolo_save_path)
