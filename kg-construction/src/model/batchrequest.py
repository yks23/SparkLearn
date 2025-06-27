import json
from zhipuai import ZhipuAI
import time
import logging as log
class BatchRequest:
    def __init__(self, custom_id: str, model: str, system_prompt: str, user_input: str):
        self.custom_id = custom_id
        self.method = "POST"
        self.url = "/v4/chat/completions"
        self.body = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            "temperature": 0.1
        }
        

    def to_dict(self) -> dict:
        """将结构体转换为字典格式"""
        return {
            "custom_id": self.custom_id,
            "method": self.method,
            "url": self.url,
            "body": self.body
        }
class BatchRequestManager:
    def __init__(self, system_prompt: str, user_input: list,model: str,file_path: str,api_key:str):
        self.system_prompt = system_prompt
        self.user_input = user_input
        self.model = model
        self.file_path=file_path
        self.client=ZhipuAI(api_key=api_key)
    def create_batch_requests_file(self):
        batchlist = []
        for i,user_input in enumerate(self.user_input):
            custom_id = f"{self.model}_{i}"
            batchlist.append(BatchRequest(custom_id, self.model, self.system_prompt, user_input).to_dict())
        with open(self.file_path, 'w', encoding='utf-8') as file:
            for batch_request in batchlist:
                # 每行写入一个 JSON 对象，不需要缩进
                file.write(json.dumps(batch_request, ensure_ascii=False) + '\n')
    def upload_batch_requests_file(self):
        result=self.client.files.create(file=open(self.file_path,'rb'),purpose="batch")
        return result
    def batch_request(self,file_id: str):
        log.info(f"开始创建批处理任务:{file_id}")
        create = self.client.batches.create(
            input_file_id=file_id,
            endpoint="/v4/chat/completions", 
            auto_delete_input_file=False,
        )
        log.info(f"批处理任务创建成功，任务ID: {create.id}")
        return create
    
    def get_batch_result(self, batch_id: str, max_retries: int = 60, interval: int = 60):
        """
        获取批处理任务结果，包含自动轮询逻辑
        
        Args:
            batch_id: 批处理任务ID
            max_retries: 最大重试次数，默认60次
            interval: 轮询间隔（秒），默认60秒
            
        Returns:
            批处理任务结果
            
        Raises:
            Exception: 当任务最终失败或超出重试次数时抛出
        """
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                batch_job = self.client.batches.retrieve(batch_id)
                status = batch_job.status
                
                if status == "completed":
                    
                    return batch_job
                    
                elif status in ["failed", "expired", "cancelled"]:
                    raise Exception(f"批处理任务异常终止，状态: {status}")
                    
                elif status in ["validating", "in_progress", "finalizing", "cancelling"]:
                    print(f"任务进行中，当前状态: {status}，等待{interval}秒后重试...")
                    time.sleep(interval)
                    retry_count += 1
                    continue
                    
                else:
                    raise Exception(f"未知的任务状态: {status}")
                    
            except Exception as e:
                if "任务进行中" not in str(e):
                    raise Exception(f"获取批处理结果失败: {str(e)}")
                if retry_count >= max_retries - 1:
                    raise Exception(f"获取批处理结果超时，已重试{max_retries}次")
                retry_count += 1
                
        raise Exception(f"获取批处理结果超时，已重试{max_retries}次")
    def download_and_transform(self,file_id: str):
        content=self.client.files.content(file_id)
        result_file_path=self.file_path.split(".")[0]+"_result.jsonl"
        content.write_to_file(result_file_path)
        response_data=[]
        with open(result_file_path,'r',encoding='utf-8') as file:
            for line in file:
                data=json.loads(line)
                response_content = data['response']['body']['choices'][0]['message']['content']
                response_data.append(response_content)
        return response_data
    def work_whole_step(self):
        self.create_batch_requests_file()
        with open(self.file_path.split('.')[0]+"_batch_info.txt","w",encoding="utf-8") as file:
            file_id=self.upload_batch_requests_file().id
            file.write(file_id+"\n")
            batch_id=self.batch_request(file_id).id
            file.write(batch_id+"\n")
            file_id=self.get_batch_result(batch_id).output_file_id
            file.write(file_id+"\n")
        return self.download_and_transform(file_id)

