import os
from typing import List, Dict, Generator
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, api_key: str = None, model: str = "glm-4"):
        self.api_key = api_key
        self.model_name = model

    def chat_completion(self, messages: List[Dict[str, str]], api_key_override: str = None) -> Generator:
        api_key = api_key_override or self.api_key
        
        if not api_key:
            yield "错误: 未配置 API Key，请在 app_flask.py 中填写。"
            return

        # 硅基流动或 OpenAI 兼容格式 (sk-...)
        if api_key.startswith("sk-"):
            logger.info(f"使用 OpenAI 兼容模式，模型: {self.model_name}")
            yield from self._chat_openai_compatible(api_key, messages)
        # Gemini 格式 (AIza...)
        else:
            logger.info(f"使用 Gemini 模式，模型: {self.model_name}")
            yield from self._chat_gemini(api_key, messages)

    def _chat_openai_compatible(self, api_key: str, messages: List[Dict[str, str]]) -> Generator:
        try:
            from openai import OpenAI
            
            # 硅基流动 (SiliconFlow) 的官方地址
            base_url = "https://api.siliconflow.cn/v1"
            
            logger.info(f"正在请求硅基流动地址: {base_url}")
            
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"硅基流动调用出错: {str(e)}")
            yield f"API 调用出错 (401通常为地址不匹配或Key失效): {str(e)}"

    def _chat_gemini(self, api_key: str, messages: List[Dict[str, str]]) -> Generator:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # 提取所有系统消息作为模型指令
            system_instructions = "\n".join([m["content"] for m in messages if m["role"] == "system"])
            model = genai.GenerativeModel(self.model_name, system_instruction=system_instructions)
            
            history = []
            # 过滤掉系统消息，只保留 user/assistant 消息作为对话历史
            chat_messages = [m for m in messages if m["role"] != "system"]
            
            for msg in chat_messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})
            
            chat = model.start_chat(history=history)
            response = chat.send_message(chat_messages[-1]["content"], stream=True)
            for chunk in response:
                try:
                    if chunk.text:
                        yield chunk.text
                except:
                    yield "[生成内容被拦截]"
        except Exception as e:
            yield f"Gemini 模式调用出错: {str(e)}"
