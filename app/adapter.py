import time
import asyncio
from app.config import logger

class AdapterCore:
    def __init__(self, api_key: str, model_name: str, config: dict, http_client):
        self.api_key = api_key
        self.model_name = model_name
        self.config = config
        self.client = http_client

    async def handle_async_polling(self, prompt, size, urls=None, extra_params=None):
        driver = None
        for d_id, d_cfg in self.config["drivers"].items():
            if self.model_name in d_cfg.get("models", []):
                driver = d_cfg
                break
        
        if not driver: 
            raise ValueError(f"Unsupported model: '{self.model_name}'")

        target_url = driver["submit_urls"].get(self.model_name)
        if not target_url:
            raise Exception(f"Submit URL not found for model: {self.model_name}")
        
        payload = {"key": self.api_key, "prompt": prompt}
        if urls:
            payload["urls"] = urls
        if extra_params:
            for k, v in extra_params.items():
                if k not in payload:
                    payload[k] = v
            
        # 动态参数映射处理
        model_params = driver.get("model_params", {}).get(self.model_name)
        if model_params:
            size_map = model_params.get("size_mapping", {})
            mapped_size = size_map.get(size, size_map.get("default", size))
            
            size_field = model_params.get("size_field", "size")
            payload[size_field] = mapped_size
            
            # urls 格式自动转换 (数组还是单字符串)
            if "urls" in payload:
                urls_format = model_params.get("urls_format", "array")
                if urls_format == "string" and isinstance(payload["urls"], list) and len(payload["urls"]) > 0:
                    payload["urls"] = payload["urls"][0]
            
            # 添加模型需要的其他固定参数
            for k, v in model_params.get("fixed_params", {}).items():
                payload[k] = v
        else:
            payload["size"] = size

        # 1. 提交
        headers = {"Authorization": self.api_key}
        res = await self.client.post(target_url, headers=headers, json=payload)
        
        if res.status_code != 200:
            raise Exception(f"Provider HTTP {res.status_code}: {res.text}")
            
        data = res.json()
        if data.get("code") != 200: raise Exception(data.get("msg", "Submit failed"))
        
        task_id = data["data"]["id"]
        
        # 2. 轮询
        start = time.time()
        interval = driver.get("polling_interval", 3)
        timeout = driver.get("timeout", 120)
        error_count = 0
        
        while time.time() - start < timeout:
            await asyncio.sleep(interval)
            try:
                poll_res = await self.client.get(driver["poll_url"], params={"key": self.api_key, "id": task_id})
                if poll_res.status_code != 200:
                    raise Exception(f"Poll HTTP {poll_res.status_code}: {poll_res.text}")
                    
                p_data = poll_res.json()
                if p_data.get("code") == 200 and p_data.get("data"):
                    content = p_data["data"]
                    
                    # 优先尝试获取最终 URL
                    res_field = content.get("result") or content.get("url") or content.get("image_url")
                    
                    if res_field:
                        if isinstance(res_field, list) and len(res_field) > 0:
                            return res_field[0]
                        elif isinstance(res_field, str):
                            return res_field
                            
                    # 检测是否有明确的失败状态 (排除 0, 1 等进行中状态)
                    status = content.get("status")
                    if status not in [None, 0, 1] and content.get("message"):
                        raise Exception(f"Provider task failed: {content.get('message')}")
                
                # 正常响应则重置错误计数器
                error_count = 0
            except Exception as e:
                error_count += 1
                logger.error(f"Polling exception for task {task_id} (Attempt {error_count}): {e}")
                if error_count >= 3:
                    raise Exception(f"Upstream provider unavailable after 3 attempts: {e}")
                continue
        return None
