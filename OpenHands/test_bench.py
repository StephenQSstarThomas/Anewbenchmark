#!/usr/bin/env python3
"""
OpenHands Agent 测试运行程序

该程序从config.toml读取配置，从test.json读取问题描述，
然后运行OpenHands agent来解决问题。instance_id用于追踪和记录。

使用方法:
    python test_run.py                              # 使用默认设置(max_iterations=10)
    python test_run.py --max-iterations 20          # 设置最大迭代次数为20
    python test_run.py --config my_config.toml      # 指定配置文件
    python test_run.py --test my_test.json          # 指定测试文件
    python test_run.py --file prompt.txt            # 从文本文件读取prompt内容
    python test_run.py --help                       # 显示帮助信息

重要参数:
    --max-iterations: 限制agent的最大步数，防止无限运行 (默认: 10)
"""

import asyncio
import json
import sys
import argparse
import os
from pathlib import Path
from datetime import datetime

# OpenHands imports
from openhands.core.config import load_openhands_config, OpenHandsConfig
from openhands.core.main import run_controller
from openhands.events.action import MessageAction
from openhands.core.logger import openhands_logger as logger
os.environ["RUN_AS_OPENHANDS"] = "false"

def load_config(config_path: str = "./config.toml", max_iterations: int = 10):
    """从TOML文件加载OpenHands配置"""
    config_path = Path(config_path).resolve()
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    print(f"加载配置文件: {config_path}")
    
    # 使用OpenHands的官方配置加载函数
    config = load_openhands_config(config_file=str(config_path))
    
    # 设置最大迭代次数限制，防止agent无限运行
    config.max_iterations = max_iterations
    print(f"设置最大迭代次数: {max_iterations}")
    
    return config


def load_test_problem(test_path: str = "./test.json") -> dict:
    """从JSON文件加载测试问题"""
    test_path = Path(test_path).resolve()
    
    if not test_path.exists():
        raise FileNotFoundError(f"测试文件不存在: {test_path}")
    
    print(f"加载测试文件: {test_path}")
    
    with open(test_path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    # test.json是一个包含测试用例的列表，我们取第一个
    if isinstance(test_data, list) and len(test_data) > 0:
        return test_data[0]
    elif isinstance(test_data, dict):
        return test_data
    else:
        raise ValueError("测试文件格式不正确")


def load_prompt_from_file(file_path: str) -> str:
    """从文本文件加载prompt内容"""
    file_path = Path(file_path).resolve()
    
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt文件不存在: {file_path}")
    
    print(f"加载Prompt文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    if not content:
        raise ValueError("Prompt文件内容为空")
    
    return content


def create_prompt(problem_statement: str) -> str:
    """创建给agent的完整prompt（不包含instance_id）"""
    
    TASK_INSTRUCTION = """
Given the following GitHub problem description, your objective is to localize the specific files, classes or functions, and lines of code that need modification or contain key information to resolve the issue.
"""
    
    prompt = f"""
{TASK_INSTRUCTION}

**Problem Statement:**
{problem_statement}

Please analyze the problem and provide a detailed solution including:
1. Identification of relevant files and code locations
2. Specific modifications needed
3. Step-by-step implementation plan
"""
    
    return prompt


async def run_openhands_agent(config: OpenHandsConfig, prompt: str, instance_id: str) -> str:
    """运行OpenHands agent"""
    
    print("=" * 80)
    print(f"开始运行OpenHands Agent")
    print(f"Instance ID (用于追踪): {instance_id}")
    print(f"最大迭代次数限制: {config.max_iterations}")
    print("=" * 80)
    
    # 创建初始的用户消息action
    initial_action = MessageAction(content=prompt)
    
    # 设置session ID，包含instance_id用于追踪
    sid = f"instance_{instance_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # 记录instance_id到日志中
        logger.info(f"开始处理实例: {instance_id}")
        
        # 运行controller
        final_state = await run_controller(
            config=config,
            initial_user_action=initial_action,
            sid=sid,
            headless_mode=True,
            exit_on_message=False
        )
        
        # 记录完成信息
        logger.info(f"实例 {instance_id} 处理完成")
        
        print("=" * 80)
        print("Agent 运行完成!")
        print(f"Instance ID: {instance_id}")
        print("=" * 80)
        
        if final_state:
            # 尝试获取最后的动作，如果没有则显示状态信息
            try:
                if hasattr(final_state, 'last_action'):
                    print(f"最终状态: {final_state.last_action}")
                elif hasattr(final_state, 'history') and final_state.history:
                    print(f"最终状态: 共执行了 {len(final_state.history)} 个步骤")
                else:
                    print(f"最终状态: Agent已完成运行")
            except Exception as e:
                print(f"最终状态: Agent已完成运行 (状态获取异常: {e})")
            
            # 查找轨迹保存位置
            trajectory_path = config.save_trajectory_path
            if trajectory_path:
                trajectory_file = Path(trajectory_path) / f"{sid}.json"
                print(f"轨迹文件保存位置: {trajectory_file}")
                
                # 在轨迹文件中添加instance_id信息
                if trajectory_file.exists():
                    try:
                        with open(trajectory_file, 'r') as f:
                            trajectory_data = json.load(f)
                        
                        # 添加instance_id到轨迹数据
                        # 处理轨迹数据可能是列表或字典的情况
                        if isinstance(trajectory_data, dict):
                            trajectory_data['instance_id'] = instance_id
                            trajectory_data['session_id'] = sid
                        elif isinstance(trajectory_data, list):
                            # 如果是列表，添加一个元数据对象
                            metadata = {
                                'instance_id': instance_id,
                                'session_id': sid,
                                'metadata_type': 'trajectory_info'
                            }
                            trajectory_data.append(metadata)
                        else:
                            # 如果是其他类型，创建新的包装结构
                            new_data = {
                                'original_data': trajectory_data,
                                'instance_id': instance_id,
                                'session_id': sid
                            }
                            trajectory_data = new_data
                        
                        with open(trajectory_file, 'w') as f:
                            json.dump(trajectory_data, f, indent=2)
                        
                        print(f"已在轨迹文件中记录 Instance ID: {instance_id}")
                    except Exception as e:
                        logger.warning(f"无法更新轨迹文件的instance_id: {e}")
                
                return str(trajectory_file)
            else:
                print("未配置轨迹保存路径")
                return ""
        else:
            print("Agent运行失败，没有返回最终状态")
            return ""
            
    except Exception as e:
        print(f"运行Agent时出错: {e}")
        logger.error(f"实例 {instance_id} 运行失败: {e}", exc_info=True)
        return ""


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="OpenHands Agent 测试运行程序")
    parser.add_argument("--max-iterations", type=int, default=10, 
                        help="最大迭代次数 (默认: 10)")
    parser.add_argument("--config", type=str, default="./config.toml",
                        help="配置文件路径 (默认: ./config.toml)")
    parser.add_argument("--test", type=str, default="./test.json", 
                        help="测试文件路径 (默认: ./test.json)")
    parser.add_argument("--prompt", type=str, default=None,
                        help="直接指定prompt内容，如果提供则忽略test.json文件")
    parser.add_argument("--file", type=str, default=None,
                        help="指定包含prompt内容的文件路径(txt格式)，如果提供则忽略test.json和--prompt参数")
    args = parser.parse_args()
    
    print("OpenHands Agent 测试运行程序")
    print("=" * 80)
    print(f"最大迭代次数限制: {args.max_iterations}")
    print("=" * 80)
    
    try:
        # 1. 加载配置
        config = load_config(args.config, args.max_iterations)
        print(f"配置加载成功")
        # 获取第一个LLM配置
        llm_config = next(iter(config.llms.values())) if config.llms else None
        if llm_config:
            print(f"  - 模型: {llm_config.model}")
        print(f"  - Agent: {config.default_agent}")
        print(f"  - 最大迭代次数: {config.max_iterations}")
        print(f"  - 轨迹保存路径: {config.save_trajectory_path}")
        
        # 2. 处理输入（来自--file、--prompt参数或test.json文件）
        if args.file:
            # 使用从文件读取的prompt
            prompt = load_prompt_from_file(args.file)
            instance_id = f"file_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            repo = "unknown"
            print(f"\n使用从文件读取的prompt:")
            print(f"  - 文件路径: {args.file}")
            print(f"  - Instance ID: {instance_id}")
            print(f"  - Prompt内容: {prompt[:200]}...")
        elif args.prompt:
            # 使用直接提供的prompt
            prompt = args.prompt
            instance_id = f"prompt_injection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            repo = "unknown"
            print(f"\n使用直接提供的prompt:")
            print(f"  - Instance ID: {instance_id}")
            print(f"  - Prompt内容: {prompt[:200]}...")
        else:
            # 从test.json文件加载
            test_problem = load_test_problem(args.test)
            problem_statement = test_problem.get("problem_statement", "")
            instance_id = test_problem.get("instance_id", "unknown")
            repo = test_problem.get("repo", "unknown")
            
            print(f"\n测试问题加载成功:")
            print(f"  - Instance ID: {instance_id}")
            print(f"  - Repository: {repo}")
            print(f"  - 问题描述: {problem_statement[:200]}...")
            
            # 3. 创建prompt（不包含instance_id）
            prompt = create_prompt(problem_statement)
        
        # 4. 运行agent（instance_id用于追踪和记录）
        trajectory_file = asyncio.run(run_openhands_agent(config, prompt, instance_id))
        
        # 5. 输出结果
        print("\n" + "=" * 80)
        print("运行完成!")
        print(f"Instance ID: {instance_id}")
        if trajectory_file:
            print(f"Agent轨迹保存在: {trajectory_file}")
            print("轨迹文件中包含instance_id信息用于追踪")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n用户中断了程序运行")
        sys.exit(1)
    except Exception as e:
        print(f"程序运行出错: {e}")
        logger.error(f"主程序异常: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
