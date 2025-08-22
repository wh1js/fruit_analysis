import base64
import requests
import os

def baidu_seg_two_images(image_path1, image_path2):
    API_URL = "https://z179nf7b7atc6dm5.aistudio-hub.baidu.com/instance-segmentation"
    # 请前往 https://aistudio.baidu.com/index/accessToken 查看“访问令牌”并替换
    TOKEN = "6382cad74c452f2aea435944da565988fe4c38a2"
    output_image_path_list=[]
    # Determine the predict folder number
    base_dir = "model_runs_results/baidu_seg_runs"
    predict_num = 1
    while True:
        predict_dir = f"predict{predict_num}"
        if not os.path.exists(os.path.join(base_dir, predict_dir)):
            os.makedirs(os.path.join(base_dir, predict_dir), exist_ok=True)
            break
        predict_num += 1
        #print("SEG : SEG RESULT HAS BEEN GET TO model_runs_results/baidu_seg_runs/predict{}".format(predict_num))
    damage=0
    for idx, image_path in enumerate([image_path1, image_path2]):
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
        payload = {"image": image_data}  # Base64编码的文件内容

        # 调用API
        response = requests.post(API_URL, json=payload, headers=headers)

        # 处理接口返回数据
        assert response.status_code == 200
        result = response.json()["result"]
        #print(response.json())

        # 保存输出图像
        output_image_path = os.path.join(base_dir, predict_dir, f"out{idx+1}.jpg")
        output_image_path_list.append(output_image_path)
        with open(output_image_path, "wb") as file:
            file.write(base64.b64decode(result["image"]))
        #print(f"Output image saved at {output_image_path}")
        for i in result["instances"]:
            damage_s=i['mask']['size'][0]*i['mask']['size'][1]*0.8
            damage+=damage_s
    return damage,output_image_path_list

if __name__ == "__main__":
    image1 = "upload_images/1754984861/image_0.jpg"
    image2 = "upload_images/1754984861/image_2.jpg"
    damage_s_all,seg_output_image_path=baidu_seg_two_images(image1, image2)
    print(damage_s_all)
    print("seg_output_image_path:",seg_output_image_path)