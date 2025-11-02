#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
各大模型API调用对比示例
本文件总结了主流大模型API的免费额度、价格、优劣势，并提供Python调用示例
"""

import os
import time
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator

# 环境变量配置（实际使用时请替换为自己的API密钥）
API_KEYS = {
    'openai': os.getenv('OPENAI_API_KEY', 'your_openai_api_key'),
    'claude': os.getenv('ANTHROPIC_API_KEY', 'your_anthropic_api_key'),
    'wenxin': os.getenv('WENXIN_API_KEY', 'your_wenxin_api_key'),
    'qianwen': os.getenv('QIANWEN_API_KEY', 'your_qianwen_api_key'),
    'xinghuo': os.getenv('XINGHUO_API_KEY', 'your_xinghuo_api_key'),
    'deepseek': os.getenv('DEEPSEEK_API_KEY', 'your_deepseek_api_key'),
    'grok': os.getenv('GROK_API_KEY', 'your_grok_api_key'),
}

"""
第一部分：各大模型API免费额度和价格对比（2025年最新数据）
"""

MODEL_COMPARISON = {
    # 国外模型
    'OpenAI': {
        'models': {
            'GPT-3.5 Turbo': {
                'input_price': 0.5,  # 每百万tokens价格（元）
                'output_price': 1.5,  # 每百万tokens价格（元）
                'free_credit': '新用户注册可能获得5-18美元免费额度，有效期3个月',
                'context_window': '16K-128K tokens',
                'features': ['多模态', '函数调用', 'JSON模式']
            },
            'GPT-4o': {
                'input_price': 10,  # 每百万tokens价格（元）
                'output_price': 30,  # 每百万tokens价格（元）
                'free_credit': '无直接免费额度',
                'context_window': '128K tokens',
                'features': ['多模态', '函数调用', 'JSON模式', '高级推理']
            },
            'GPT-4 Turbo': {
                'input_price': 70,  # 每百万tokens价格（元）
                'output_price': 140,  # 每百万tokens价格（元）
                'free_credit': '无直接免费额度',
                'context_window': '128K tokens',
                'features': ['多模态', '函数调用', 'JSON模式', '高级推理']
            }
        },
        'pros': ['生态完善', '模型效果领先', '开发者工具丰富', '社区支持强大'],
        'cons': ['价格较高', '有访问限制', '需要信用卡验证', 'API不稳定']
    },
    'Claude (Anthropic)': {
        'models': {
            'Claude 3 Haiku': {
                'input_price': 3,  # 每百万tokens价格（元）
                'output_price': 15,  # 每百万tokens价格（元）
                'free_credit': '新用户注册可能获得少量免费额度',
                'context_window': '200K tokens',
                'features': ['长文本处理', '函数调用', '多语言支持']
            },
            'Claude 3 Sonnet': {
                'input_price': 15,  # 每百万tokens价格（元）
                'output_price': 75,  # 每百万tokens价格（元）
                'free_credit': '无直接免费额度',
                'context_window': '200K tokens',
                'features': ['长文本处理', '函数调用', '多语言支持', '高级推理']
            },
            'Claude 3 Opus': {
                'input_price': 75,  # 每百万tokens价格（元）
                'output_price': 375,  # 每百万tokens价格（元）
                'free_credit': '无直接免费额度',
                'context_window': '200K tokens',
                'features': ['长文本处理', '函数调用', '多语言支持', '顶级推理能力']
            }
        },
        'pros': ['长上下文处理', '内容安全性高', '中文支持好', '工具调用能力强'],
        'cons': ['价格高', 'API调用复杂', '需要信用卡验证', '服务不稳定']
    },
    'Grok (xAI)': {
        'models': {
            'Grok-2': {
                'input_price': None,  # 具体价格未明确
                'output_price': None,  # 具体价格未明确
                'free_credit': '到2024年底每月25美元免费额度，绑定卡并充值5美元后可获得',
                'context_window': '128K tokens',
                'features': ['函数调用', '系统提示词支持']
            }
        },
        'pros': ['API兼容OpenAI和Anthropic', '马斯克旗下产品', '免费额度可观'],
        'cons': ['模型效果有待验证', '需要信用卡', '服务可用性不稳定']
    },
    
    # 国内模型
    '百度文心一言': {
        'models': {
            'ERNIE Speed': {
                'input_price': 0,  # 免费
                'output_price': 0,  # 免费
                'free_credit': '2025年4月1日起全面免费',
                'context_window': '未明确',
                'features': ['中文优化', '多模态支持', '工具调用']
            },
            'ERNIE Lite': {
                'input_price': 0,  # 免费
                'output_price': 0,  # 免费
                'free_credit': '2025年4月1日起全面免费',
                'context_window': '未明确',
                'features': ['中文优化', '轻量化']
            },
            '文心4.0系列': {
                'input_price': 0,  # 免费
                'output_price': 0,  # 免费
                'free_credit': '2025年4月1日起全面免费',
                'context_window': '未明确',
                'features': ['深度搜索', '高级推理', '多模态处理']
            }
        },
        'pros': ['全面免费', '中文支持极佳', '国内访问速度快', '合规性高'],
        'cons': ['国际通用性较差', 'API文档相对复杂', '高级功能有限']
    },
    '阿里通义千问': {
        'models': {
            'Qwen1.5-7B': {
                'input_price': 1,  # 每百万tokens价格（元）
                'output_price': 2,  # 每百万tokens价格（元）
                'free_credit': '新用户可能有免费试用额度',
                'context_window': '32K tokens',
                'features': ['开源模型', '中文优化']
            },
            'Qwen-Long': {
                'input_price': 0.5,  # 每百万tokens价格（元）
                'output_price': 2,  # 每百万tokens价格（元）
                'free_credit': '新用户可能有免费试用额度',
                'context_window': '超长上下文',
                'features': ['长文本处理', '中文优化']
            }
        },
        'pros': ['价格低廉', '中文支持好', '稳定性高', '阿里生态整合'],
        'cons': ['模型效果相对国际顶尖模型略有差距', 'API功能相对简单']
    },
    '科大讯飞星火': {
        'models': {
            '星火Lite': {
                'input_price': 0,  # 免费
                'output_price': 0,  # 免费
                'free_credit': '永久免费',
                'context_window': '未明确',
                'features': ['基础对话', '文本生成']
            },
            '星火Pro/Max': {
                'input_price': 21,  # 每百万tokens价格（元）
                'output_price': 21,  # 每百万tokens价格（元）
                'free_credit': '个人200万tokens/月，企业500万tokens/月',
                'context_window': '未明确',
                'features': ['高级对话', '多模态', '工具调用']
            }
        },
        'pros': ['Lite版永久免费', '语音处理优势', '国内访问稳定', '合规性高'],
        'cons': ['高级版价格相对较高', '模型迭代较慢']
    },
    'DeepSeek': {
        'models': {
            'DeepSeek-V2': {
                'input_price': 1,  # 每百万tokens价格（元）
                'output_price': 2,  # 每百万tokens价格（元）
                'free_credit': '部分功能免费',
                'context_window': '32K tokens',
                'features': ['性价比高', '代码能力强', '中文优化']
            },
            'DeepSeek-V3': {
                'input_price': 8,  # 优惠期每百万tokens价格（元）
                'output_price': 8,  # 优惠期每百万tokens价格（元）
                'free_credit': '部分功能免费',
                'context_window': '未明确',
                'features': ['性能接近GPT-4o', '中文优化', '代码能力强']
            }
        },
        'pros': ['价格极低', '模型效果好', '代码能力突出', '中文支持佳'],
        'cons': ['API稳定性有待提高', '功能相对有限']
    },
    '腾讯混元': {
        'models': {
            '混元高级版': {
                'input_price': 100,  # 每百万tokens价格（元）
                'output_price': 100,  # 每百万tokens价格（元）
                'free_credit': '可能有免费试用额度',
                'context_window': '未明确',
                'features': ['中文优化', '腾讯生态整合']
            }
        },
        'pros': ['腾讯生态整合', '国内访问稳定', '合规性高'],
        'cons': ['价格相对较高', '功能和效果有待提升']
    }
}

"""
第二部分：大模型API调用示例
"""

# OpenAI API调用示例
def openai_api_example(prompt: str, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
    """
    OpenAI API调用示例
    
    Args:
        prompt: 用户提问内容
        model: 使用的模型名称
    
    Returns:
        包含回复内容的字典
    """
    # 注意：实际使用时需要安装OpenAI库: pip install openai
    try:
        import openai
        
        openai.api_key = API_KEYS['openai']
        
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个有用的AI助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return {
            "status": "success",
            "response": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# OpenAI 流式输出示例
async def openai_streaming_example(prompt: str, model: str = "gpt-3.5-turbo") -> AsyncGenerator[str, None]:
    """
    OpenAI流式输出示例
    
    Args:
        prompt: 用户提问内容
        model: 使用的模型名称
    
    Yields:
        生成的文本片段
    """
    try:
        import openai
        
        openai.api_key = API_KEYS['openai']
        
        stream = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个有用的AI助手。"},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            temperature=0.7,
            max_tokens=1000
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"错误: {str(e)}"

# Claude API调用示例
def claude_api_example(prompt: str, model: str = "claude-3-sonnet-20240229") -> Dict[str, Any]:
    """
    Claude API调用示例
    
    Args:
        prompt: 用户提问内容
        model: 使用的模型名称
    
    Returns:
        包含回复内容的字典
    """
    # 注意：实际使用时需要安装anthropic库: pip install anthropic
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=API_KEYS['claude'])
        
        message = client.messages.create(
            model=model,
            max_tokens=1000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return {
            "status": "success",
            "response": message.content[0].text,
            "usage": {
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "total_tokens": message.usage.input_tokens + message.usage.output_tokens
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# 百度文心一言API调用示例
def wenxin_api_example(prompt: str, model: str = "ERNIE-Bot-4") -> Dict[str, Any]:
    """
    百度文心一言API调用示例
    
    Args:
        prompt: 用户提问内容
        model: 使用的模型名称
    
    Returns:
        包含回复内容的字典
    """
    # 注意：实际使用时需要安装文心一言SDK: pip install erniebot
    try:
        import erniebot
        
        erniebot.api_type = 'aistudio'  # 或 'qianfan'
        erniebot.access_token = API_KEYS['wenxin']
        
        response = erniebot.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return {
            "status": "success",
            "response": response.result,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# 阿里通义千问API调用示例
def qianwen_api_example(prompt: str, model: str = "qwen-max") -> Dict[str, Any]:
    """
    阿里通义千问API调用示例
    
    Args:
        prompt: 用户提问内容
        model: 使用的模型名称
    
    Returns:
        包含回复内容的字典
    """
    # 注意：实际使用时需要安装通义千问SDK: pip install dashscope
    try:
        import dashscope
        
        dashscope.api_key = API_KEYS['qianwen']
        
        response = dashscope.Generation.call(
            model=model,
            prompt=prompt,
            temperature=0.7,
            max_tokens=1000
        )
        
        return {
            "status": "success",
            "response": response.output.text,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# 科大讯飞星火API调用示例
def xinghuo_api_example(prompt: str, app_id: str, api_key: str, api_secret: str) -> Dict[str, Any]:
    """
    科大讯飞星火API调用示例
    
    Args:
        prompt: 用户提问内容
        app_id: 应用ID
        api_key: API密钥
        api_secret: API密钥
    
    Returns:
        包含回复内容的字典
    """
    # 注意：星火API需要自己实现websocket连接或使用第三方库
    try:
        # 这里提供一个简化的HTTP API调用示例
        import requests
        import hashlib
        import base64
        import hmac
        import time
        import json
        
        # 生成认证信息
        timestamp = str(int(time.time()))
        signature_origin = f"host: api.xf-yun.com\ndate: {timestamp}\nPOST /v1/private/sse HTTP/1.1"
        signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(signature_sha).decode('utf-8')
        authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        headers = {
            'Authorization': authorization,
            'Content-Type': 'application/json',
            'host': 'api.xf-yun.com',
            'date': timestamp
        }
        
        data = {
            "header": {
                "app_id": app_id,
                "uid": "test_user"
            },
            "parameter": {
                "chat": {
                    "domain": "general",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            },
            "payload": {
                "message": {
                    "text": [{"role": "user", "content": prompt}]
                }
            }
        }
        
        response = requests.post('https://api.xf-yun.com/v1/private/sse',
                               headers=headers,
                               json=data)
        
        # 解析响应
        result = json.loads(response.content)
        return {
            "status": "success",
            "response": result['payload']['choices']['text'][0]['content'],
            "usage": {}
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# DeepSeek API调用示例
def deepseek_api_example(prompt: str, model: str = "deepseek-chat") -> Dict[str, Any]:
    """
    DeepSeek API调用示例
    
    Args:
        prompt: 用户提问内容
        model: 使用的模型名称
    
    Returns:
        包含回复内容的字典
    """
    try:
        import requests
        import json
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEYS['deepseek']}"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个有用的AI助手。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        return {
            "status": "success",
            "response": result['choices'][0]['message']['content'],
            "usage": result.get('usage', {})
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Grok API调用示例
def grok_api_example(prompt: str, model: str = "grok-beta") -> Dict[str, Any]:
    """
    Grok API调用示例（兼容OpenAI API格式）
    
    Args:
        prompt: 用户提问内容
        model: 使用的模型名称
    
    Returns:
        包含回复内容的字典
    """
    try:
        import requests
        import json
        
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEYS['grok']}"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个有用的AI助手。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        return {
            "status": "success",
            "response": result['choices'][0]['message']['content'],
            "usage": result.get('usage', {})
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# 通用大模型调用接口
class LLMClient:
    """
    通用大模型客户端，支持多种模型的调用
    """
    
    def __init__(self, model_type: str = "openai", **kwargs):
        """
        初始化客户端
        
        Args:
            model_type: 模型类型，可选值：openai, claude, wenxin, qianwen, xinghuo, deepseek, grok
            **kwargs: 其他参数
        """
        self.model_type = model_type
        self.kwargs = kwargs
        
        # 设置API密钥
        if model_type in API_KEYS and not kwargs.get(f"{model_type}_api_key"):
            self.kwargs[f"{model_type}_api_key"] = API_KEYS[model_type]
    
    def chat(self, prompt: str, **options) -> Dict[str, Any]:
        """
        发送聊天请求
        
        Args:
            prompt: 用户提问内容
            **options: 可选参数
        
        Returns:
            包含回复内容的字典
        """
        if self.model_type == "openai":
            return openai_api_example(prompt, options.get("model", "gpt-3.5-turbo"))
        elif self.model_type == "claude":
            return claude_api_example(prompt, options.get("model", "claude-3-sonnet-20240229"))
        elif self.model_type == "wenxin":
            return wenxin_api_example(prompt, options.get("model", "ERNIE-Bot-4"))
        elif self.model_type == "qianwen":
            return qianwen_api_example(prompt, options.get("model", "qwen-max"))
        elif self.model_type == "xinghuo":
            return xinghuo_api_example(
                prompt,
                self.kwargs.get("app_id", ""),
                self.kwargs.get("xinghuo_api_key", ""),
                self.kwargs.get("api_secret", "")
            )
        elif self.model_type == "deepseek":
            return deepseek_api_example(prompt, options.get("model", "deepseek-chat"))
        elif self.model_type == "grok":
            return grok_api_example(prompt, options.get("model", "grok-beta"))
        else:
            return {"status": "error", "error": f"不支持的模型类型: {self.model_type}"}
    
    async def stream_chat(self, prompt: str, **options) -> AsyncGenerator[str, None]:
        """
        流式聊天请求
        
        Args:
            prompt: 用户提问内容
            **options: 可选参数
        
        Yields:
            生成的文本片段
        """
        if self.model_type == "openai":
            async for chunk in openai_streaming_example(prompt, options.get("model", "gpt-3.5-turbo")):
                yield chunk
        else:
            # 其他模型的流式实现可以在这里添加
            yield "当前模型暂不支持流式输出"

"""
第三部分：模型选择建议和使用场景
"""

MODEL_RECOMMENDATIONS = {
    "budget_limited": ["百度文心一言", "科大讯飞星火Lite", "DeepSeek-V2"],  # 价格最优惠选择
    "chinese_performance": ["百度文心一言", "阿里通义千问", "DeepSeek"],  # 中文表现最佳
    "advanced_reasoning": ["GPT-4o", "Claude 3 Opus", "DeepSeek-V3"],  # 高级推理能力
    "long_context": ["Claude 3 Sonnet", "GPT-4o", "阿里通义千问Qwen-Long"],  # 长文本处理
    "code_generation": ["DeepSeek", "GPT-4o", "Claude 3 Sonnet"],  # 代码生成
    "multimodal": ["GPT-4o", "Claude 3 Opus", "百度文心一言"],  # 多模态能力
    "api_stability": ["OpenAI", "百度文心一言", "阿里通义千问"],  # API稳定性
}

# 测试函数
def test_llm_client():
    """
    测试LLMClient的基本功能
    """
    print("=== 大模型API调用示例测试 ===")
    print("注意：请先设置相应的API密钥环境变量")
    print()
    
    # 选择一个模型进行测试
    # 这里默认使用OpenAI模型，实际使用时可以替换为其他模型
    try:
        client = LLMClient(model_type="openai")
        print("正在调用OpenAI API...")
        result = client.chat("你好，请简要介绍一下自己")
        
        if result["status"] == "success":
            print("\n响应结果:")
            print(result["response"])
            print("\n使用统计:")
            print(f"输入token: {result['usage'].get('prompt_tokens', 'N/A')}")
            print(f"输出token: {result['usage'].get('completion_tokens', 'N/A')}")
            print(f"总token: {result['usage'].get('total_tokens', 'N/A')}")
        else:
            print(f"错误: {result['error']}")
            print("提示: 可能需要设置API密钥或检查网络连接")
    except Exception as e:
        print(f"测试失败: {str(e)}")
    
    print("\n=== 测试完成 ===")
    print("要测试其他模型，请在代码中修改LLMClient的初始化参数")

# 打印模型比较表格
def print_model_comparison():
    """
    打印模型比较表格
    """
    print("=" * 80)
    print("各大模型API免费额度和价格对比")
    print("=" * 80)
    
    for provider, info in MODEL_COMPARISON.items():
        print(f"\n{provider}:")
        print("-" * 60)
        print(f"优点: {', '.join(info['pros'])}")
        print(f"缺点: {', '.join(info['cons'])}")
        print()
        print("  模型详情:")
        print("  " + "-" * 50)
        print("  {:<20} {:<15} {:<15} {:<20}".format("模型名称", "输入价格(百万token)", "输出价格(百万token)", "免费额度"))
        print("  " + "-" * 50)
        
        for model_name, model_info in info['models'].items():
            input_price = model_info['input_price'] if model_info['input_price'] is not None else "未知"
            output_price = model_info['output_price'] if model_info['output_price'] is not None else "未知"
            free_credit = model_info['free_credit'][:30] + "..." if len(model_info['free_credit']) > 30 else model_info['free_credit']
            
            print(f"  {:<20} {:<15} {:<15} {:<20}".format(
                model_name, 
                str(input_price) + ("元" if isinstance(input_price, (int, float)) else ""),
                str(output_price) + ("元" if isinstance(output_price, (int, float)) else ""),
                free_credit
            ))

if __name__ == "__main__":
    # 打印模型比较信息
    print_model_comparison()
    print()
    
    # 运行测试
    test_llm_client()

    # 打印使用建议
    print("\n=== 模型选择建议 ===")
    for scenario, models in MODEL_RECOMMENDATIONS.items():
        print(f"{scenario.replace('_', ' ').title()}: {', '.join(models)}")
    
    print("\n=== 使用说明 ===")
    print("1. 本脚本提供了各大模型的API调用示例")
    print("2. 使用前请设置相应的API密钥环境变量")
    print("3. 可以使用LLMClient类来统一调用不同的模型")
    print("4. 价格信息可能会变动，请以官方最新价格为准")
    print("5. 百度文心一言自2025年4月1日起全面免费")
    print("6. DeepSeek提供极高的性价比，价格仅为GPT-4 Turbo的约1%")