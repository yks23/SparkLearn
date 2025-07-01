import base64, json, time, hashlib, hmac, requests

class XunfeiOCR:
    def __init__(self, appid, api_keys: dict):
        self.appid = appid
        self.api_keys = api_keys

        self.api_endpoints = {
            'printed':      ('https://webapi.xfyun.cn/v1/service/v1/ocr/general', 'md5'),
            'handwritten':  ('https://webapi.xfyun.cn/v1/service/v1/ocr/handwriting', 'md5'),
            'formula':      ('https://rest-api.xfyun.cn/v2/itr', 'hmac'),
            'doc_restore':  ('wss: //ws-api.xf-yun.com/v1/private/ma008db16', 'hmac')
        }

    def image_to_base64(self, image_path):
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def get_headers(self, ocr_type, param_dict):
        assert ocr_type in self.api_endpoints, f"Unsupported OCR type: {ocr_type}"
        api_key = self.api_keys[ocr_type]['api_key']
        x_param = base64.b64encode(json.dumps(param_dict).encode('utf-8')).decode('utf-8')
        x_time = str(int(time.time()))

        sign_mode = self.api_endpoints[ocr_type][1]

        if sign_mode == 'md5':
            raw = api_key + x_time + x_param
            x_checksum = hashlib.md5(raw.encode('utf-8')).hexdigest()
        elif sign_mode == 'hmac':
            api_secret = self.api_keys[ocr_type]['api_secret']
            raw = self.appid + x_time + x_param
            x_checksum = base64.b64encode(
                hmac.new(api_secret.encode('utf-8'), raw.encode('utf-8'), digestmod=hashlib.sha256).digest()
            ).decode('utf-8')
        else:
            raise ValueError("Unknown sign mode")

        return {
            'X-CurTime': x_time,
            'X-Param': x_param,
            'X-Appid': self.appid,
            'X-CheckSum': x_checksum,
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
        }

    def recognize(self, image_path, ocr_type='printed'):
        url, _ = self.api_endpoints[ocr_type]
        param_dict = {
            "engine_type": "recognize_document" if ocr_type == 'doc_restore' else "general",
            "language": "cn|en",
        }
        image_base64 = self.image_to_base64(image_path)
        headers = self.get_headers(ocr_type, param_dict)
        data = {'image': image_base64}
        response = requests.post(url, headers=headers, data=data, verify=False) #  Python 3.10 + OpenSSL 3.0.2 在 Ubuntu / WSL 环境下的一种兼容性问题，主要是某些 HTTPS证书的签名算法 与 OpenSSL 的默认配置不兼容。不知道反正先改成false了
        return response.json()

appid = "b97bb794"
api_keys = {
    'printed':     {'api_key': '03b0f6ec7474dc586fcf0439d939de15'},
    'handwritten': {'api_key': '03b0f6ec7474dc586fcf0439d939de15'},
    'formula':     {'api_key': 'c87bad1f164b70337becc4d833246d17', 'api_secret': 'Y2ExMGViM2RjMjdjNmZhNjkyNjZkZDhi'},
    'doc_restore': {'api_key': 'c87bad1f164b70337becc4d833246d17', 'api_secret': 'Y2ExMGViM2RjMjdjNmZhNjkyNjZkZDhi'}
}

ocr = XunfeiOCR(appid, api_keys)
result = ocr.recognize(r"./source/formula_text.png", ocr_type='formula')
print(json.dumps(result, indent=2, ensure_ascii=False))
