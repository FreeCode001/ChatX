"""
接入硅基流动平台大模型，初始化对话模型
"""
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from .model_utils import sf_model_mapping, zp_model_mapping, load_custom_model_config,get_custom_model_mapping

load_dotenv()

# 初始化对话模型
#ZP_GLM-4.7-Flash
def init_model(temperature=0.7, model_name="SF_Qwen3-8B"):
    try:
        mark = model_name.split("_")[0]
        if mark == "SF":
            model_id = sf_model_mapping.get(model_name, model_name.replace("SF_", ""))
            model = init_chat_model(
                api_key = os.getenv("sf_api_key"),
                base_url = os.getenv("sf_api_url"),
                model = model_id,
                model_provider = "openai",
                temperature = temperature,
                max_tokens = 64000,
            )
        elif mark == "ZP":
            model_id = zp_model_mapping.get(model_name, model_name.replace("ZP_", ""))
            model = init_chat_model(
                api_key = os.getenv("zp_api_key"),
                base_url = os.getenv("zp_api_url"),
                model = model_id,
                model_provider = "openai",
                temperature = temperature,
                max_tokens = 64000,
            )
        elif mark == "PRIVATE":
            all_user_models = load_custom_model_config()
            model_id = model_name.replace("PRIVATE_", "")
            private_api_key = ""
            private_api_url = ""
            provider = "openai"
            max_tokens = 64000
            for item in all_user_models:
                if item.get("model_name") == model_name:
                    model_id = item.get("model_id", model_name.replace("PRIVATE_", ""))
                    private_api_key = item.get("api_key","")
                    private_api_url = item.get("base_url","")
                    provider = item.get("provider","openai")
                    max_tokens = item.get("max_tokens", 64000)
                    break
            model = init_chat_model(
                api_key = private_api_key,
                base_url = private_api_url,
                model = model_id,
                model_provider = provider,
                temperature = temperature,
                max_tokens = max_tokens,
            )
        else:
            model = init_chat_model(
                api_key = os.getenv("sf_api_key"),
                base_url = os.getenv("sf_api_url"),
                model = model_name,
                model_provider = "openai",
                temperature = temperature,
                max_tokens = 64000,
            )
        return model
    except Exception as e:
        print(f"模型初始化失败: {e}")
        return None
        

# 获取所有可用模型（内置 + 自定义）
def get_available_models(username: str|None = None):
    # 内置模型
    built_in_models = dict(sf_model_mapping, **zp_model_mapping)
    
    # 自定义模型
    custom_models = get_custom_model_mapping(username)
    
    # 合并并返回所有模型
    return dict(built_in_models, **custom_models)



# 测试模型初始化
if __name__ == "__main__":
    model = init_model()
    res=model.invoke("你好")
    print(res)