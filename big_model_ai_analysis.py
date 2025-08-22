#非流式
import os
from openai import OpenAI
from typing import Tuple
import sys
import re


def extract_values(input_string):
  # Extract text value
  text_match = re.search(r'"text":\s*"(.*?)(?<!\\)"', input_string, re.DOTALL)
  text_value = text_match.group(1) if text_match else ""

  # Extract quality value
  quality_match = re.search(r'"quality":\s*"(.*?)(?<!\\)"', input_string)
  quality_value = quality_match.group(1) if quality_match else ""

  # Extract solving value
  solving_match = re.search(r'"solving":\s*"(.*?)(?<!\\)"', input_string, re.DOTALL)
  solving_value = solving_match.group(1) if solving_match else ""

  return text_value, quality_value, solving_value
def big_model_ai_analysis(input_json):
    client = OpenAI(
         #api_key='766db1161c641fc86b98207681df4b6a89e81898',  # 含有 AI Studio 访问令牌，https://aistudio.baidu.com/account/accessToken,
          api_key='6382cad74c452f2aea435944da565988fe4c38a2',
         base_url="https://aistudio.baidu.com/llm/lmapi/v3",  # aistudio 大模型 api 服务域名
    )
    #适合生长范围：空气温度[15–20°C]、土壤湿度[60–80%]、土壤温度[15–25°C]、土壤氮[0.1–0.2%]、土壤有效磷[20–50 mg/kg]、土壤有效钾[100–200 mg/kg]、土壤pH[5.5–6.5]。  不适合生长范围：空气温度（低于-5°C，高于35°C）、土壤湿度（低于40%，高于90%或积水）、土壤温度（低于5°C，高于30°C）、土壤氮（低于0.05%，高于0.3%）、土壤有效磷（低于10 mg/kg，高于100 mg/kg）、土壤有效钾（低于50 mg/kg，高于300 mg/kg）、土壤pH（低于5.0，高于7.5）
    #适合生长范围：空气温度[15–20°C]、空气湿度[60–80%]、土壤湿度[60–80%]、土壤温度[15–25°C]、土壤氮[0.1–0.2%]、土壤有效磷[20–50 mg/kg]、土壤有效钾[100–200 mg/kg]、土壤pH[5.5–6.5]、光照强度[10000–30000 lx]、空气二氧化碳含量[350–600 ppm] 不适合生长范围：空气温度(低于-5°C，高于35°C)、空气湿度(低于40%，高于90%)、土壤湿度(低于40%，高于90%或积水)、土壤温度(低于5°C，高于30°C)、土壤氮(低于0.05%，高于0.3%)、土壤有效磷(低于10 mg/kg，高于100 mg/kg)、土壤有效钾(低于50 mg/kg，高于300 mg/kg)、土壤pH(低于5.0，高于7.5)、光照强度(低于5000 lx，高于50000 lx)、空气二氧化碳含量(低于200 ppm，高于1000 ppm)
    system_content={
        "text": "你扮演的角色是枇杷品质检测专家，提取输入的字典中的PH、水分、糖度值、黑点数、果径值、总损伤面积、空气温度、空气湿度、土壤湿度、土壤温度、土壤湿度、土壤氮、磷、钾含量、土壤ph、光照强度、空气二氧化碳含量值等，请严格根据输入的input_json的数据对枇杷生成品质总结。\n用户输入数据json内容包括通过基于飞桨框架CNN-LSTM网络预测的PH、水分、糖度值，PP-YOLOE_plus-S检测的黑点数、果径值，Mask-RT-DETR-H分隔的总损伤面积、空气温度、土壤湿度、土壤温度、土壤湿度、土壤氮、磷、钾含量、土壤ph值等。\n处理流程：1. 识别输入中的水果状态（PH、水分、糖度、黑点数、果径、损伤面积、品质）、环境参数(空气温度、土壤湿度、土壤温度、土壤湿度、土壤氮、磷、钾含量、土壤ph值)检测值及关键词。2. 糖度分四级：低甜度（0-5）、中等甜度（5-12）、高甜度（12-20）、超高甜度（20-999）；果径分四级：小果（0-3）、中果（3-4）、大果（4-5）、特大果（5-10）。环境参数：适合生长范围：空气温度[15–20°C]、空气湿度[60–80%]、土壤湿度[60–80%]、土壤温度[15–25°C]、土壤氮[0.1–0.2%]、土壤有效磷[20–50 mg/kg]、土壤有效钾[100–200 mg/kg]、土壤pH[5.5–6.5]、光照强度[10000–30000 lx]、空气二氧化碳含量[350–600 ppm] 不适合生长范围：空气温度(低于-5°C，高于35°C)、空气湿度(低于40%，高于90%)、土壤湿度(低于40%，高于90%或积水)、土壤温度(低于5°C，高于30°C)、土壤氮(低于0.05%，高于0.3%)、土壤有效磷(低于10 mg/kg，高于100 mg/kg)、土壤有效钾(低于50 mg/kg，高于300 mg/kg)、土壤pH(低于5.0，高于7.5)、光照强度(低于5000 lx，高于50000 lx)、空气二氧化碳含量(低于200 ppm，高于1000 ppm) 3. 结合检测值与预训练数据，根据环境因素(空气温度、土壤湿度、土壤温度、土壤湿度、土壤氮、磷、钾含量、土壤ph值)参考数据，分析偏低或偏高因素，提出培育建议（如增肥、补光、加水）。4. 使用专业语言分析6个参数（PH、水分、糖度、黑点数、果径、损伤面积），6个参数以1,2,3,4,5,6分段，每个参数换行输出，以总分总结构输出至text字段。5. 总结品质为优质、良好、一般、较差，置于quality字段。6.总结改进措施，输出环境参数中所有不符合我给出标准的参数的改进措施，置于solving字段。\n输出为JSON，包含text和quality字段，text限200字符，不含markdown，段间以\\n换行。",
        "example_response":"1.该枇杷糖度为8.86百利，属中等甜度，风味适中，建议增加光照、控制温度、施肥。2.PH值为3.85，偏酸，符合枇杷类果实酸度特性，控制土壤ph值。3.水分含量高达91.5%，表明果实新鲜度良好，水分供应充分。4.黑点数为25个，过多，请保证温度适宜！。5.擦伤面积仅为0.05cm²，表明外观轻微受损，对整体品质影响有限。6.果径为5.15cm，属特大果，表明生长周期良好，营养供应充足。建议适当控制采后处理过程以降低表皮损伤，提升外观评分。整体来看，该枇杷水分充足、果径优越，糖酸协调，外观略有瑕疵，品质评定为良好。 ",
        "quality":"良好",
        "solving":"1.当前空气温度在22.7-23.3℃，不适应枇杷生长，请调整。2.空气二氧化碳含量过高。3.空气湿度过低。4.增加肥料，增加氮磷钾含量。5.枇杷果实偏酸，请控制土壤ph值。3.4.5."
        }

    chat_completion = client.chat.completions.create(
        messages=[
            {'role': 'system', 'content': '{}'.format(system_content)},
            {"role": "user", "content":"{}".format(input_json)}
        ],
        model="ernie-4.0-turbo-128k",
    )
    #ernie-4.0-turbo-128k
    #deepseek-r1
    # print(chat_completion.choices[0].message.reasoning_content)
    text, quality, solving = extract_values(chat_completion.choices[0].message.content)
    return text, quality, solving


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
if __name__ == '__main__':
  json = {
    "枇杷数据": {
      "pH值": 3.96,
      "水分": 93.12,
      "糖度": 6.61,
      "黑点数": 1,
      "果径": 4.3,
      "损伤面积": 3
    },
    "环境数据": {
      "空气温度": [
        22.8,
        23.1,
        23,
        22.9,
        23.2,
        22.7,
        23.3,
        22.9,
        23,
        23.1
      ],
      "空气湿度": [
        55.8,
        56,
        56.3,
        56.5,
        56.2,
        56.4,
        56.1,
        55.9,
        56.3,
        56.2
      ],
      "土壤氮含量": [
        0.2,
        0.1,
        0.3,
        0.4,
        0.2,
        0.1,
        0.3,
        0.2,
        0.5,
        0.3
      ],
      "土壤温度": [
        20.8,
        21,
        21.1,
        21.3,
        21.2,
        21.4,
        21,
        20.9,
        21.3,
        21.1
      ],
      "土壤湿度": [
        91.5,
        91.9,
        91.7,
        91.8,
        91.6,
        92,
        91.8,
        91.9,
        91.6,
        91.7
      ],
      "土壤钾含量": [
        21.5,
        22.2,
        22,
        21.8,
        22.3,
        21.7,
        22.1,
        22,
        21.9,
        22.4
      ],
      "土壤盐分": [
        19.5,
        20.1,
        20.3,
        19.8,
        20,
        19.7,
        20.2,
        19.9,
        20.4,
        20.1
      ],
      "土壤磷含量": [
        0.3,
        0.2,
        0.1,
        0.5,
        0.4,
        0.3,
        0.6,
        0.2,
        0.4,
        0.5
      ],
      "土壤电阻": [
        39.5,
        40.2,
        40.1,
        39.8,
        40,
        40.3,
        39.9,
        40.5,
        40.4,
        40.1
      ],
      "空气光照强度": [
        87,
        88,
        86,
        89,
        90,
        88,
        87,
        89,
        88,
        90
      ],
      "空气二氧化碳": [
        1105,
        1110,
        1115,
        1120,
        1118,
        1122,
        1112,
        1116,
        1120,
        1119
      ],
      "土壤pH": [
        7.2,
        7.3,
        7.1,
        7.4,
        7.2,
        7.3,
        7.1,
        7.2,
        7.3,
        7.2
      ]
    }
  }  # 这与生成报告的json的字典的需要保持一直
  input_json=process_json_data(json)
  w,x,b=big_model_ai_analysis(input_json)
  print("x=",x)

