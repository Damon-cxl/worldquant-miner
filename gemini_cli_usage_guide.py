#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gemini CLI 调用指南
本文件详细介绍如何通过 Python 使用 Gemini CLI 以及 Python 库调用 Gemini 模型
"""

import os
import subprocess
import sys
import time
from typing import Optional, Dict, Any, List

"""
第一部分：Gemini CLI 安装与配置
"""

# Gemini CLI 安装命令
GEMINI_CLI_INSTALL_COMMANDS = {
    "npm": "npm install -g @google/gemini-cli",
    "npm_specific_version": "npm install -g @google/gemini-cli@0.6.1",  # 安装特定版本
    "pip": "pip install gemini-cli"  # 另一种 Python 包安装方式
}

# 验证安装命令
GEMINI_CLI_VERIFY_COMMANDS = {
    "version": "gemini --version",
    "about": "gemini /about",
    "help": "gemini /help"
}


def install_gemini_cli(method: str = "npm") -> bool:
    """
    安装 Gemini CLI
    
    Args:
        method: 安装方法，支持 "npm" 或 "pip"
    
    Returns:
        bool: 安装是否成功
    """
    try:
        if method == "npm":
            print("使用 npm 安装 Gemini CLI...")
            subprocess.run(GEMINI_CLI_INSTALL_COMMANDS["npm"], shell=True, check=True)
        elif method == "npm_specific":
            print("使用 npm 安装特定版本的 Gemini CLI (0.6.1)...")
            subprocess.run(GEMINI_CLI_INSTALL_COMMANDS["npm_specific_version"], shell=True, check=True)
        elif method == "pip":
            print("使用 pip 安装 Python gemini-cli 包...")
            subprocess.run(GEMINI_CLI_INSTALL_COMMANDS["pip"], shell=True, check=True)
        else:
            print(f"不支持的安装方法: {method}")
            return False
        
        print("Gemini CLI 安装成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Gemini CLI 安装失败: {e}")
        print("请确保已安装 Node.js (npm) 或 Python (pip) 并配置正确")
        return False


def verify_gemini_cli() -> Dict[str, str]:
    """
    验证 Gemini CLI 安装和配置
    
    Returns:
        Dict[str, str]: 验证结果
    """
    results = {}
    for cmd_name, cmd in GEMINI_CLI_VERIFY_COMMANDS.items():
        try:
            print(f"执行命令: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                results[cmd_name] = "成功"
                print(f"{cmd_name}: 成功")
                if cmd_name == "version":
                    print(f"版本信息: {result.stdout.strip()}")
                elif cmd_name == "about":
                    print(f"模型信息:\n{result.stdout.strip()}")
            else:
                results[cmd_name] = f"失败: {result.stderr.strip()}"
                print(f"{cmd_name}: 失败")
                print(f"错误信息: {result.stderr.strip()}")
        except Exception as e:
            results[cmd_name] = f"错误: {str(e)}"
            print(f"{cmd_name}: 发生错误 - {str(e)}")
    return results


def setup_gemini_api_key(api_key: str) -> bool:
    """
    设置 Gemini API 密钥到环境变量
    
    Args:
        api_key: Gemini API 密钥
    
    Returns:
        bool: 设置是否成功
    """
    try:
        # 在当前进程中设置环境变量
        os.environ["GEMINI_API_KEY"] = api_key
        
        # 对于 Windows，可以设置用户环境变量
        if sys.platform == "win32":
            subprocess.run(
                f"setx GEMINI_API_KEY \"{api_key}\"", 
                shell=True, 
                check=True,
                capture_output=True,
                text=True
            )
            print("已设置 Windows 用户环境变量 GEMINI_API_KEY")
            print("注意：新的环境变量需要在新的命令提示符或 PowerShell 窗口中生效")
        else:
            # 对于 Unix/Linux/Mac，可以添加到 .bashrc 或 .zshrc
            rc_file = os.path.expanduser("~/.bashrc")
            if os.path.exists(rc_file):
                with open(rc_file, "a") as f:
                    f.write(f"\nexport GEMINI_API_KEY=\"{api_key}\"\n")
                print(f"已将 GEMINI_API_KEY 添加到 {rc_file}")
                print("请运行 'source ~/.bashrc' 使环境变量立即生效")
            else:
                print("已在当前进程中设置 GEMINI_API_KEY")
        
        print("API 密钥设置成功！")
        return True
    except Exception as e:
        print(f"API 密钥设置失败: {e}")
        return False

"""
第二部分：通过 Python 调用 Gemini CLI
"""


def run_gemini_cli_command(prompt: str, model: Optional[str] = None) -> str:
    """
    通过 Python 运行 Gemini CLI 命令
    
    Args:
        prompt: 要发送给 Gemini 的提示
        model: 可选，指定使用的模型
    
    Returns:
        str: Gemini 的响应
    """
    try:
        # 构建命令
        cmd = ["gemini"]
        if model:
            cmd.extend(["-m", model])
        cmd.append(prompt)
        
        # 运行命令
        print(f"执行 Gemini CLI 命令: {cmd}")
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"错误: {result.stderr.strip()}"
    except Exception as e:
        return f"执行错误: {str(e)}"


def gemini_cli_interactive_session():
    """
    启动交互式 Gemini CLI 会话
    """
    print("启动 Gemini CLI 交互式会话...")
    print("输入 'exit' 或 'quit' 退出会话")
    print("输入 '/help' 查看可用命令")
    print("-" * 50)
    
    try:
        # 使用 subprocess.Popen 启动交互式会话
        process = subprocess.Popen(
            ["gemini"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        
        # 读取初始输出
        initial_output = process.stdout.readline()
        if initial_output:
            print(initial_output.strip())
        
        # 交互式循环
        while True:
            # 获取用户输入
            user_input = input("你: ")
            
            if user_input.lower() in ["exit", "quit", ":q", "bye"]:
                print("退出会话...")
                process.stdin.write("\n")
                process.stdin.flush()
                time.sleep(0.5)
                process.terminate()
                break
            
            # 发送输入给 Gemini
            process.stdin.write(user_input + "\n")
            process.stdin.flush()
            
            # 读取并显示响应
            response = ""
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                response += line
                print(line.strip())
                # 检查是否到达响应结束
                if line.strip().endswith("gemini>"):
                    break
    
    except KeyboardInterrupt:
        print("\n会话被用户中断")
    except Exception as e:
        print(f"会话发生错误: {str(e)}")

"""
第三部分：使用 Python 库调用 Gemini API
"""


def install_google_generativeai() -> bool:
    """
    安装 Google Generative AI Python 库
    
    Returns:
        bool: 安装是否成功
    """
    try:
        print("安装 google-generativeai Python 库...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", "google-generativeai"],
            check=True,
            capture_output=True,
            text=True
        )
        print("google-generativeai 安装成功！")
        return True
    except Exception as e:
        print(f"google-generativeai 安装失败: {e}")
        return False


def call_gemini_with_python(api_key: str, prompt: str, model_name: str = "gemini-pro") -> Dict[str, Any]:
    """
    使用 Python 库调用 Gemini API
    
    Args:
        api_key: Gemini API 密钥
        prompt: 用户提示
        model_name: 模型名称，默认为 "gemini-pro"
    
    Returns:
        Dict[str, Any]: 包含响应和使用情况的字典
    """
    try:
        import google.generativeai as genai
        
        # 配置 API 密钥
        genai.configure(api_key=api_key)
        
        # 创建模型实例
        model = genai.GenerativeModel(model_name)
        
        # 生成内容
        response = model.generate_content(prompt)
        
        # 解析响应
        result = {
            "status": "success",
            "response": response.text,
            "usage": {
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "candidates_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count
            }
        }
        
        return result
    except ImportError:
        return {"status": "error", "error": "请先安装 google-generativeai 库: pip install -U google-generativeai"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def call_gemini_streaming(api_key: str, prompt: str, model_name: str = "gemini-pro") -> List[str]:
    """
    使用 Python 库流式调用 Gemini API
    
    Args:
        api_key: Gemini API 密钥
        prompt: 用户提示
        model_name: 模型名称，默认为 "gemini-pro"
    
    Returns:
        List[str]: 生成的文本片段列表
    """
    try:
        import google.generativeai as genai
        
        # 配置 API 密钥
        genai.configure(api_key=api_key)
        
        # 创建模型实例
        model = genai.GenerativeModel(model_name)
        
        # 流式生成内容
        response_chunks = []
        for chunk in model.generate_content(prompt, stream=True):
            if chunk.text:
                response_chunks.append(chunk.text)
                print(chunk.text, end="", flush=True)
        print()  # 输出换行
        
        return response_chunks
    except ImportError:
        print("错误: 请先安装 google-generativeai 库")
        return ["请先安装 google-generativeai 库: pip install -U google-generativeai"]
    except Exception as e:
        return [f"错误: {str(e)}"]


def list_available_gemini_models(api_key: str) -> List[Dict[str, str]]:
    """
    列出可用的 Gemini 模型
    
    Args:
        api_key: Gemini API 密钥
    
    Returns:
        List[Dict[str, str]]: 可用模型列表
    """
    try:
        import google.generativeai as genai
        
        # 配置 API 密钥
        genai.configure(api_key=api_key)
        
        # 列出支持内容生成的模型
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models.append({
                    "name": m.name,
                    "description": m.description,
                    "generation_methods": m.supported_generation_methods
                })
        
        return models
    except Exception as e:
        print(f"获取模型列表失败: {str(e)}")
        return [{"error": str(e)}]

"""
第四部分：综合示例和使用建议
"""


def gemini_cli_python_demo(api_key: Optional[str] = None):
    """
    Gemini CLI 和 Python API 调用演示
    
    Args:
        api_key: 可选，Gemini API 密钥
    """
    print("=" * 60)
    print("Gemini CLI 和 Python API 调用演示")
    print("=" * 60)
    
    # 设置 API 密钥
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("警告: 未设置 GEMINI_API_KEY 环境变量")
        print("请在使用 Python API 调用前设置 API 密钥")
    else:
        print("已检测到 GEMINI_API_KEY 环境变量")
    
    # 演示 1: 使用 Gemini CLI 命令行调用
    print("\n" + "-" * 60)
    print("演示 1: 使用 Gemini CLI 命令行调用")
    print("-" * 60)
    
    test_prompt = "请用中文简要介绍一下 Gemini 模型"
    print(f"\n发送提示: {test_prompt}")
    cli_response = run_gemini_cli_command(test_prompt)
    print("\nGemini CLI 响应:")
    print(cli_response)
    
    # 演示 2: 使用 Python API 调用（如果有 API 密钥）
    if api_key:
        print("\n" + "-" * 60)
        print("演示 2: 使用 Python API 调用")
        print("-" * 60)
        
        print("\n检查 google-generativeai 库是否已安装...")
        try:
            import google.generativeai as genai
            print("google-generativeai 库已安装")
            
            # 列出可用模型
            print("\n可用的 Gemini 模型:")
            models = list_available_gemini_models(api_key)
            for i, model in enumerate(models):
                print(f"{i+1}. {model['name']}")
                if 'description' in model:
                    print(f"   描述: {model['description']}")
            
            # 调用模型
            print("\n使用 Python API 调用 Gemini:")
            python_response = call_gemini_with_python(api_key, test_prompt)
            if python_response["status"] == "success":
                print("\nPython API 响应:")
                print(python_response["response"])
                print("\n使用统计:")
                print(f"提示词 tokens: {python_response['usage']['prompt_tokens']}")
                print(f"回答 tokens: {python_response['usage']['candidates_tokens']}")
                print(f"总 tokens: {python_response['usage']['total_tokens']}")
            else:
                print(f"调用失败: {python_response['error']}")
                
            # 演示流式调用
            print("\n演示流式输出:")
            print("流式响应:")
            call_gemini_streaming(api_key, "请用中文写出 5 个简短的励志句子，每个句子占一行")
                
        except ImportError:
            print("google-generativeai 库未安装")
            install_choice = input("是否要安装 google-generativeai 库? (y/n): ")
            if install_choice.lower() == 'y':
                if install_google_generativeai():
                    print("库安装成功，可以重新运行此演示")
    
    # 提供交互式会话选项
    print("\n" + "-" * 60)
    print("演示完成")
    print("-" * 60)
    print("\n您可以:")
    print("1. 运行 interactive_session() 启动交互式 Gemini CLI 会话")
    print("2. 使用 call_gemini_with_python() 通过 Python 库调用 Gemini")
    print("3. 使用 run_gemini_cli_command() 通过 Python 调用 Gemini CLI")


def create_config_example():
    """
    创建配置示例文件
    """
    config_example = """
# Gemini API 配置示例

# 1. API 密钥设置方法:
# Windows:
# setx GEMINI_API_KEY "your_api_key_here"

# Linux/Mac:
# export GEMINI_API_KEY="your_api_key_here"
# 或添加到 ~/.bashrc

# 2. Gemini CLI 常用命令:
gemini --version            # 查看版本
gemini /about               # 查看模型信息
gemini /help                # 查看帮助
gemini "你的问题"           # 简单查询
gemini -m gemini-1.5-pro "你的问题"  # 指定模型

# 3. Python API 调用配置:
# 安装: pip install -U google-generativeai
# 配置: import google.generativeai as genai
#      genai.configure(api_key="your_api_key_here")

# 4. 获取 API 密钥:
# 访问 https://ai.google.dev/ 获取 Gemini API 密钥
# 新用户可能获得免费额度
    """
    
    config_path = "gemini_config_example.txt"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_example.strip())
        print(f"已创建配置示例文件: {config_path}")
    except Exception as e:
        print(f"创建配置示例文件失败: {e}")

# 主函数
def main():
    """
    主函数，提供交互式菜单
    """
    while True:
        print("\n" + "=" * 60)
        print("Gemini 调用工具")
        print("=" * 60)
        print("1. 安装 Gemini CLI")
        print("2. 验证 Gemini CLI 安装")
        print("3. 设置 Gemini API 密钥")
        print("4. 运行演示")
        print("5. 启动交互式会话")
        print("6. 创建配置示例")
        print("0. 退出")
        print("=" * 60)
        
        choice = input("请选择操作 (0-6): ")
        
        if choice == "1":
            method = input("选择安装方法 (npm/pip/npm_specific): ").strip().lower()
            if method not in ["npm", "pip", "npm_specific"]:
                method = "npm"  # 默认使用 npm
            install_gemini_cli(method)
        
        elif choice == "2":
            verify_gemini_cli()
        
        elif choice == "3":
            api_key = input("请输入 Gemini API 密钥: ").strip()
            if api_key:
                setup_gemini_api_key(api_key)
            else:
                print("API 密钥不能为空")
        
        elif choice == "4":
            api_key_input = input("请输入 Gemini API 密钥 (可选，如果已设置环境变量则直接回车): ").strip()
            api_key = api_key_input if api_key_input else None
            gemini_cli_python_demo(api_key)
        
        elif choice == "5":
            gemini_cli_interactive_session()
        
        elif choice == "6":
            create_config_example()
        
        elif choice == "0":
            print("感谢使用，再见！")
            break
        
        else:
            print("无效的选择，请重新输入")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    main()