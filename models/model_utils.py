import os
import sys
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
import yaml
from yaml.loader import SafeLoader
from chatxweb.auth import get_user_roles

# ChatX 内置模型
## 1. 硅基流动
sf_model_mapping = {
            "SF_Qwen3-8B": "Qwen/Qwen3-8B",
            "SF_DeepSeek-R1-8B": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            "SF_DeepSeek-R1-7B": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
            "SF_GLM-4-9B": "THUDM/GLM-4-9B-0414",
            "SF_GLM-Z1-9B": "THUDM/GLM-Z1-9B-0414",
            "SF_GLM-4-9B-Chat": "THUDM/glm-4-9b-chat",
            "SF_DeepSeeek-OCR": "deepseek-ai/DeepSeek-OCR",
            "SF_Hunyuan-MT-7B": "tencent/Hunyuan-MT-7B",
            "SF_GLM-4.1V-9B-Thinking": "THUDM/GLM-4.1V-9B-Thinking", 
            "SF_SenseVoiceSmall": "FunAudioLLM/SenseVoiceSmall", # 语音识别模型
        }

## 2. 智谱模型
zp_model_mapping = {
            "ZP_GLM-4.7-Flash": "GLM-4.7-Flash", #免费文本模型
            "ZP_GLM-4-Flash-250414": "GLM-4-Flash-250414", #免费模型
            "ZP_GLM-4.6V-Flash": "GLM-4.6V-Flash", #免费模型，视觉理解模型
            "ZP_GLM-Z1-Flash": "GLM-Z1-Flash", #免费模型，推理模型
            "ZP_CogView-3-Flash": "CogView-3-Flash", #免费模型，图像生成
            "ZP_CogVideoX-Flash": "CogVideoX-Flash", #免费模型，视频生成
        }

## 3. 自定义模型
### 3.1 自定义模型配置文件路径
custom_model_config_path = os.path.join(os.path.dirname(__file__), '..', 'models_config.yaml')
### 3.2 加载自定义模型配置
def load_custom_model_config(username: str | None = None):
    try:
        with open(custom_model_config_path, 'r', encoding='utf-8') as f:
            res = yaml.load(f, Loader=SafeLoader)
        roles = get_user_roles(username)
        if 'admin' in roles or username == None:
            d =[]
            for item in res.get('models', {}).values():
                d.append(item)
            return d
        else:
            d =[]
            for key,value in res.get('models', {})[username].items():
                    d.append({key:value})
            return d
    except Exception as e:
        print(f"加载自定义模型配置文件失败: {e}")
        return []
### 3.3 自定义模型映射
def get_custom_model_mapping(username: str|None = None):
    res=load_custom_model_config(username)
    custom_model_mapping = {}
    if res:
        for i in res:
            for model_name, model_params in i.items():
                custom_model_mapping[model_name] = model_params.get('model_id', model_name.replace("PRIVATE_", ""))
    return custom_model_mapping


# 测试
if __name__ == "__main__":
    print(load_custom_model_config('monkey'))
    print(load_custom_model_config('yuyang'))
    print(get_custom_model_mapping('monkey'))
    print(get_custom_model_mapping('yuyang'))