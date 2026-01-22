"""
检查并创建配置文件
"""
import os
import yaml

config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

# 检查配置文件是否存在
if not os.path.exists(config_path):
    # 创建基本配置文件
    basic_config = {
        '# ChatX配置文件': '',
        '# 在此添加您的模型配置': '',
        'models': {}
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(basic_config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"配置文件已创建: {config_path}")
else:
    print(f"配置文件已存在: {config_path}")
    
    # 检查配置文件结构
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'models' not in config:
            config['models'] = {}
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            print("已在配置文件中添加models字段")
        else:
            print("配置文件结构正确")
    except Exception as e:
        print(f"配置文件读取失败: {e}")
        print("将创建新的配置文件")
        
        basic_config = {
            '# ChatX配置文件': '',
            '# 在此添加您的模型配置': '',
            'models': {}
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(basic_config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"新的配置文件已创建: {config_path}")
