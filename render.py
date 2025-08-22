from docxtpl import DocxTemplate, InlineImage
from docx.shared import Cm
import json
import time
import os
from datetime import datetime
import random
import numpy as np
import json
import re
import urllib.request
import urllib.error
from generator_lines import sp_main
from connect_image import  connect_images
sugar_rate_dict = {
    "低甜度": [0, 5],
    "中等甜度": [5, 12],
    "高甜度": [12, 20],
    "超高甜度": [20, 999],
}

diameter_rate_dict = {
    "小果": [0, 3],
    "中果": [3, 4],
    "大果": [4, 5],
    "特大果": [5, 10],
}

def avg_spectrum(spectrum_path):
    with open(spectrum_path, "r") as f:
        lines = [json.loads(line) for line in f.readlines()]
    mean_values = np.mean([[v for v in d[list(d.keys())[0]].values()] for d in lines], axis=0)
    return mean_values


def normalize_input(input_data, mean, std):
    return (input_data - mean) / std

def denormalize_output(output_data, mean, std):
    return output_data * std + mean


def get_fruit_quality(sugar, diameter):
    for k, v in sugar_rate_dict.items():
        if v[0] <= sugar < v[1]:
            sugar_status = k
            break
    for k, v in diameter_rate_dict.items():
        if v[0] <= diameter < v[1]:
            diameter_status = k
            break
    return sugar_status, diameter_status

def fetch_env_json(timeout_seconds: float = 10.0):
	"""
	请求 http://139.9.68.120:6031/fruit-curve 接口，获取JSON数据。
	- 成功时：将返回的数据保存到变量 env_json 并返回
	- 失败时：返回空字典 {}
	"""
	url = "http://139.9.68.120:6031/fruit-curve"
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Python-urllib",
		"Accept": "application/json, */*;q=0.8",
	}

	request = urllib.request.Request(url, headers=headers, method="GET")
	try:
		with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
			if getattr(response, "status", 200) != 200:
				return {}
			data_bytes = response.read()
			text = data_bytes.decode("utf-8", errors="replace")
			env_json = json.loads(text)
			if not isinstance(env_json, dict):
				# 若返回不是对象，包装为字典
				return {"data": env_json}
			return env_json
	except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
		return {}
def build_loquat_json(ph, water, sugar, damage_s_all, black, guo_len, env_json: dict) -> dict:
    """
    构建与5.py中相同结构的JSON字典。
    入参：
      - ph, water, sugar, damage_s_all, black, guo_len: 基本参数
      - env_json: 环境参数字典（英文字段）
    返回：
      - 与5.py一致结构的字典（中文键名，环境数据为原始列表）
    """

    def get_env_list(*possible_keys):
        for k in possible_keys:
            if k in env_json and isinstance(env_json[k], (list, tuple)):
                return list(env_json[k])
        return []

    result = {
        "枇杷数据": {
            "pH值": ph,
            "水分": water,
            "糖度": sugar,
            "黑点数": black,
            "果径": guo_len,
            "损伤面积": damage_s_all,
        },
        "环境数据": {
            # 空气温度
            "空气温度": get_env_list("air_temp"),
            # 空气湿度
            "空气湿度": get_env_list("air_humi", "air_hum"),
            # 土壤氮含量
            "土壤氮含量": get_env_list("element_nitrogen", "nitrogen", "dan"),
            # 土壤温度
            "土壤温度": get_env_list("ground_temp", "turang_temp"),
            # 土壤湿度
            "土壤湿度": get_env_list("ground_humi", "turang_hum"),
            # 土壤钾含量
            "土壤钾含量": get_env_list("element_potassium", "jia"),
            # 土壤盐分
            "土壤盐分": get_env_list("element_salt", "salt"),
            # 土壤磷含量
            "土壤磷含量": get_env_list("element_phosphorus", "lin", "phosphorus"),
            # 土壤电阻
            "土壤电阻": get_env_list("ground_resistance", "turang_R"),
            # 空气光照强度
            "空气光照强度": get_env_list("air_light_intensity", "guangzhao"),
            # 空气二氧化碳
            "空气二氧化碳": get_env_list("air_carbon_dioxide", "CO2"),
            # 土壤pH
            "土壤pH": get_env_list("ground_ph", "turang_ph"),
        },
    }

    return result

#这个函数在汇总的时候，需要转移到主函数中
def process_json_data(json_data):
    """
    处理JSON数据，按照指定的对照关系转换到字典中
    """
    result_dict = {}

    # 处理枇杷数据 - 直接使用数值
    pipa_data = json_data["枇杷数据"]
    result_dict["ph"] = pipa_data["pH值"]
    result_dict["water"] = pipa_data["水分"]
    result_dict["sugar"] = pipa_data["糖度"]
    result_dict["black"] = pipa_data["黑点数"]
    result_dict["guojin"] = pipa_data["果径"]
    result_dict["area"] = pipa_data["损伤面积"]

    # 处理环境数据 - 取最小值和最大值
    env_data = json_data["环境数据"]

    # 空气温度 -> air_temp
    air_tem_values = env_data["空气温度"]
    result_dict["air_temp"] = [min(air_tem_values), max(air_tem_values)]

    # 空气湿度 -> air_hum
    air_hum_values = env_data["空气湿度"]
    result_dict["air_hum"] = [min(air_hum_values), max(air_hum_values)]

    # 土壤氮含量 -> dan
    dan_values = env_data["土壤氮含量"]
    result_dict["dan"] = [min(dan_values), max(dan_values)]

    # 土壤磷含量 -> lin
    lin_values = env_data["土壤磷含量"]
    result_dict["lin"] = [min(lin_values), max(lin_values)]

    # 土壤钾含量 -> jia
    jia_values = env_data["土壤钾含量"]
    result_dict["jia"] = [min(jia_values), max(jia_values)]

    # 土壤温度 -> turang_temp
    turang_tem_values = env_data["土壤温度"]
    result_dict["turang_temp"] = [min(turang_tem_values), max(turang_tem_values)]

    # 土壤湿度 -> turang_hum
    turang_hum_values = env_data["土壤湿度"]
    result_dict["turang_hum"] = [min(turang_hum_values), max(turang_hum_values)]

    # 土壤盐分 -> salt
    salt_values = env_data["土壤盐分"]
    result_dict["salt"] = [min(salt_values), max(salt_values)]

    # 土壤电阻 -> turang_R
    turang_R_values = env_data["土壤电阻"]
    result_dict["turang_R"] = [min(turang_R_values), max(turang_R_values)]

    # 空气光照强度 -> guangzhao
    guangzhao_values = env_data["空气光照强度"]
    result_dict["guangzhao"] = [min(guangzhao_values), max(guangzhao_values)]

    # 空气二氧化碳 -> CO2
    CO2_values = env_data["空气二氧化碳"]
    result_dict["CO2"] = [min(CO2_values), max(CO2_values)]

    # 土壤pH -> turang_ph
    turang_ph_values = env_data["土壤pH"]
    result_dict["turang_ph"] = [min(turang_ph_values), max(turang_ph_values)]

    return result_dict


def render( fruit_and_env_parmeter:dict,llm_result_text, judgement,current_folder_sp,yolo_2_path,seg_2_path):

    save_path = f"generates/word/{int(time.time())}"
    os.makedirs(save_path, exist_ok=True)
    template_doc = DocxTemplate("report_render/templates/loquat_template_last.docx")
    specturm_lines_output_image_path=sp_main(current_folder_sp)
    connect_image_path=connect_images(yolo_2_path, seg_2_path)
    # template_doc = DocxTemplate("templates/loquat_template.docx")
    #spectrum_name = f"report_render/{random.randint(1, 3)}.png"
    info_dict = {
        "dangerous_image": InlineImage(template_doc, specturm_lines_output_image_path, width=Cm(14)),
        "fruit_image": InlineImage(template_doc, connect_image_path, width=Cm(14)),
        "knowledge_images": InlineImage(template_doc, "report_render/railknowledge_images/{}.png".format(random.randint(1,15)), width=Cm(14)),
        "f_pinzhi": judgement,
        "f_llm_result":str(llm_result_text),
        "clocktime_now":str(datetime.now()),
        "visit_records": [
            {
                "ph": str(round(fruit_and_env_parmeter["ph"], 2)),
                "water": str(round(fruit_and_env_parmeter["water"], 2)),
                "sugar": str(round(fruit_and_env_parmeter["sugar"], 2)),
                "black": str(fruit_and_env_parmeter["black"]),
                "guojin": str(round(fruit_and_env_parmeter["guojin"],2)),
                "area": str(round(fruit_and_env_parmeter["area"],2)),
                "air_tem":str(fruit_and_env_parmeter["air_temp"]),
                "air_hum":str(fruit_and_env_parmeter["air_hum"]),
                "turang_tem":str(fruit_and_env_parmeter["turang_temp"]),
                "turang_hum":str(fruit_and_env_parmeter["turang_hum"]),
                "dan": str(fruit_and_env_parmeter["dan"]),
                "jia": str(fruit_and_env_parmeter["jia"]),
                "lin": str(fruit_and_env_parmeter["lin"]),
                "turang_ph":str(fruit_and_env_parmeter["turang_ph"]),
                "guangzhao": str(fruit_and_env_parmeter["guangzhao"]),
                "CO2": str(fruit_and_env_parmeter["CO2"]),
                "salt": str(fruit_and_env_parmeter["salt"]),
                "turang_R": str(fruit_and_env_parmeter["turang_R"])
            }
        ]
    }
    print(info_dict)
    save_doc_path = f'{save_path}/test.docx'

    template_doc.render(info_dict)
    template_doc.save(save_doc_path)
    return save_doc_path


if __name__ == "__main__":
    env_json=fetch_env_json()
    input_json=build_loquat_json(1, 1, 1, 1, 1, 2, env_json)
    input_dict = process_json_data(input_json)
    #dict={'ph': 3.96, 'water': 93.12, 'sugar': 6.61, 'black': 1, 'guojin': 4.3, 'area': 3, 'air_temp': [22.7, 23.3], 'air_hum': [55.8, 56.5], 'dan': [0.1, 0.5], 'lin': [0.1, 0.6], 'jia': [21.5, 22.4], 'turang_temp': [20.8, 21.4], 'turang_hum': [91.5, 92], 'salt': [19.5, 20.4], 'turang_R': [39.5, 40.5], 'guangzhao': [86, 90], 'CO2': [1105, 1122], 'turang_ph': [7.1, 7.4]}
    dict=process_json_data(input_json)
    print(dict["dan"])
    render(dict,1,1,"upload_images/1754984861/specturm.txt",['model_runs_results/baidu_yolo_runs/predict14/out1.jpg', 'model_runs_results/baidu_yolo_runs/predict14/out2.jpg'],['model_runs_results/baidu_seg_runs/predict6/out1.jpg', 'model_runs_results/baidu_seg_runs/predict6/out2.jpg'])