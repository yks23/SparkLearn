
"""
  印刷文字识别WebAPI接口调用示例接口文档(必看)：https://doc.xfyun.cn/rest_api/%E5%8D%B0%E5%88%B7%E6%96%87%E5%AD%97%E8%AF%86%E5%88%AB.html
  上传图片base64编码后进行urlencode要求base64编码和urlencode后大小不超过4M最短边至少15px，最长边最大4096px支持jpg/png/bmp格式
  (Very Important)创建完webapi应用添加合成服务之后一定要设置ip白名单，找到控制台--我的应用--设置ip白名单，如何设置参考：http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=41891
  错误码链接：https://www.xfyun.cn/document/error-code (code返回错误码时必看)
  @author iflytek
"""
#-*- coding: utf-8 -*-
import requests
import time
import hashlib
import base64
import json
#from urllib import parse
# 印刷文字识别 webapi 接口地址
URL = "http://webapi.xfyun.cn/v1/service/v1/ocr/general"
# 应用ID (必须为webapi类型应用，并印刷文字识别服务，参考帖子如何创建一个webapi应用：http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=36481)
APPID = "b97bb794"
# 接口密钥(webapi类型应用开通印刷文字识别服务后，控制台--我的应用---印刷文字识别---服务的apikey)
API_KEY = "03b0f6ec7474dc586fcf0439d939de15"
def getHeader():
#  当前时间戳
    curTime = str(int(time.time()))
#  支持语言类型和是否开启位置定位(默认否)
    param = {"language": "cn|en", "location": "true"}
    param = json.dumps(param)
    paramBase64 = base64.b64encode(param.encode('utf-8'))

    m2 = hashlib.md5()
    str1 = API_KEY + curTime + str(paramBase64,'utf-8')
    m2.update(str1.encode('utf-8'))
    checkSum = m2.hexdigest()
# 组装http请求头
    header = {
        'X-CurTime': curTime,
        'X-Param': paramBase64,
        'X-Appid': APPID,
        'X-CheckSum': checkSum,
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    }
    return header


def compute_avg_word_width(data):
    widths = []
    for block in data["data"]["block"]:
        if block["type"] != "text":
            continue
        for line in block["line"]:
            for word in line["word"]:
                loc = word["location"]
                width = loc["right_bottom"]["y"] - loc["top_left"]["y"] #用的是高度
                if width > 0:
                    widths.append(width)
    if not widths:
        return 40  # fallback
    return sorted(widths)[len(widths)//2]  # 中位数更鲁棒

def parse_response_with_dynamic_indent(json_data):
    # Step 1: 提取所有 word 的坐标、字高、内容
    words = []
    for block in json_data["data"]["block"]:
        if block["type"] != "text":
            continue
        for line in block["line"]:
            for word in line["word"]:
                loc = word["location"]
                x = loc["top_left"]["x"]
                y = loc["top_left"]["y"]
                h = loc["right_bottom"]["y"] - y
                words.append({
                    "x": x,
                    "y": y,
                    "height": h,
                    "content": word["content"]
                })

    if not words:
        return ""

    # Step 2: 按 y 分组为“视觉行”，依据局部字高判断
    words.sort(key=lambda w: w["y"])
    lines = []
    current_line = []
    last_word = None

    for word in words:
        if last_word is None:
            current_line.append(word)
        else:
            delta_y = abs(word["y"] - last_word["y"])
            local_avg_height = (word["height"] + last_word["height"]) / 2
            if delta_y < local_avg_height * 0.5:
                current_line.append(word)
            else:
                lines.append(current_line)
                current_line = [word]
        last_word = word
    if current_line:
        lines.append(current_line)

    # Step 3: 构造每行文字，基于相邻 x 坐标推断空格
    result_lines = []
    for line_words in lines:
        line_words.sort(key=lambda w: w["x"])
        min_x = min(w["x"] for w in line_words)
        ref_height = sum(w["height"] for w in line_words) / len(line_words)

        indent_level = int(min_x / ref_height)
        line_text = " " * (2 * indent_level)

        for i, word in enumerate(line_words):
            line_text += word["content"]
            if i < len(line_words) - 1:
                next_x = line_words[i + 1]["x"]
                this_right = word["x"] + len(word["content"]) * word["height"] * 0.6  # 字宽估计
                gap = next_x - this_right
                gap_unit = (word["height"] + line_words[i + 1]["height"]) / 2 * 0.5
                num_spaces = int(gap / gap_unit)
                if num_spaces > 0:
                    line_text += " " * num_spaces

        result_lines.append(line_text)

    return "\n".join(result_lines)


    lines.sort(key=lambda x: x[0])
    return "\n".join(line[1] for line in lines)



# 上传文件并进行base64位编码
with open(r'./source/CS1.jpg', 'rb') as f:
    f1 = f.read()

f1_base64 = str(base64.b64encode(f1), 'utf-8')

    
data = {
        'image': f1_base64
        }


r = requests.post(URL, data=data, headers=getHeader())
result = str(r.content, 'utf-8')
# 错误码链接：https://www.xfyun.cn/document/error-code (code返回错误码时必看)
print(result)

result_json = json.loads(result)
if result_json["code"] != "0":
    print("❌ 接口调用失败：", result_json["desc"])
    exit()

md_text = parse_response_with_dynamic_indent(result_json)

# 输出到文件
with open("output.md", "w", encoding="utf-8") as f:
    f.write(md_text)

print("\n✅ 已成功输出为 output.md")

