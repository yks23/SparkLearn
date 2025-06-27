import json
import logging as log
import io

def load_json(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def attach_json(file_path: str, data):
    with open(file_path, "a", encoding="utf-8") as f:
        json.dump(data.to_dict(), f, ensure_ascii=False, indent=4)


def save_json(file_path: str, data: list):
    if len(data) == 0:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
            return
    if isinstance(data,dict):
        data_to_save = data
    elif not isinstance(data[0],dict) and not isinstance(data[0],list):
        data_to_save = [item.to_dict() if not isinstance(item,str)  else item for item in data ]
    else:
        data_to_save = data
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)


def jsonalize(data):
    
    if data.startswith("```json\n") and data.endswith("\n```"):
        data = data.split("```json\n")[1].split("\n```")[0]
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        if data.startswith("{") and data.endswith("}") or data.startswith("[") and data.endswith("]"):
            try:
                StringData = io.StringIO(data)
                StringData.seek(0)
                data = StringData.read()
                print(data)
                return json.loads(data)
            except json.JSONDecodeError:
                try:
                    data = data.replace("\\", "\\\\")
                    return json.loads(data)
                except json.JSONDecodeError:
                    log.error("JSON data decode error")
                    return json.loads(r"{}")
        else:
            last_brace_index = data.rfind("}")
            if last_brace_index != -1:
                data = data[: last_brace_index + 1] + "]}"
                try:
                    data = data.replace("\\", "\\\\")
                    return json.loads(data)
                except json.JSONDecodeError:
                    log.error("JSON data decode error")
                    return json.loads(r"{}")

