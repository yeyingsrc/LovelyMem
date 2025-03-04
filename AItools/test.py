from mailbox import Message

import asyncio
import json
from func import *
import threading
import time
from config import client

def show_loading_animation(stop_event, start_time):
    animation = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
    idx = 0
    while not stop_event.is_set():
        elapsed_time = time.time() - start_time
        print(f"\rAIlovelymem>\t [{animation[idx]}] 等待响应中... {elapsed_time:.1f}s", end="")
        idx = (idx + 1) % len(animation)
        time.sleep(0.1)
    print("\rAIlovelymem>\t 响应完成!                      ")

async def send_messages(messages,choice):
    massage = await client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tool_choice=choice,
        parallel_tool_calls=True,
        tools=tools,
        temperature=1.0
    )
    return massage.choices[0].message

tools = open(r"AItools\tools.json", "r", encoding="utf-8").read()
tools = json.loads(tools)



async def main():
    messages = [
        {"role": "system", "content": "你是一个Windows内存取证助手，你有丰富的网络安全经验，请分析以下Windows内存镜像，使用用户提供的工具进行分析，并结合用户的问题分析结果，给出简要的结论。"},
    ]
    
    print("\n[*] 欢迎使用AIlovelymem，你可以输入Q退出，输入clean清空对话")
    # get_image_info_file 打印
    mem_path, profile = get_image_info_file()
    print(f"[*] 当前内存文件路径：{mem_path}")
    print(f"[*] 当前内存系统版本(vol2有效)：{profile}")
    
    while True:
        # 用户输入
        user_input = input("\n请输入你的问题: ")
        if user_input.lower() == 'q':
            break
        if user_input.lower() == 'clean':
            messages = [messages[0]]  # 保留system消息
            print("\n[*] 对话已清空")
            continue
            
        messages.append({"role": "user", "content": user_input})
        
        # 创建并启动等待动画
        stop_event = threading.Event()
        start_time = time.time()
        animation_thread = threading.Thread(target=show_loading_animation, args=(stop_event, start_time))
        animation_thread.daemon = True
        animation_thread.start()
        
        try:
            massage = await send_messages(messages,"auto")
            stop_event.set()  # 停止动画
            animation_thread.join()
            
            if massage.tool_calls:
                messages.append(massage)
                
                for tool_call in massage.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    getfunc = globals().get(tool_call.function.name)
                    print(f"Tool name: {tool_call.function.name}")
                    print(f"Tool args: {args}")
                    try:
                        for key, value in args.items():
                            print(f"[*] {key}: {value}")
                        result = await getfunc(**args)
                    except Exception as e:
                        print(f"[-] 执行失败：{str(e)}")
                        
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        }
                    )

                # 为final_massage添加等待动画
                stop_event = threading.Event()
                start_time = time.time()
                animation_thread = threading.Thread(target=show_loading_animation, args=(stop_event, start_time))
                animation_thread.daemon = True
                animation_thread.start()

                try:
                    final_massage = await send_messages(messages,"none")
                    stop_event.set()  # 停止动画
                    animation_thread.join()
                    print(f"AIlovelymem>\t {final_massage.content}")
                    messages.append(final_massage)
                except Exception as e:
                    stop_event.set()  # 确保在发生异常时也停止动画
                    animation_thread.join()
                    print(f"[-] 执行失败：{str(e)}")
                
        except Exception as e:
            stop_event.set()  # 确保在发生异常时也停止动画
            animation_thread.join()
            print(f"[-] 执行失败：{str(e)}")


if __name__ == "__main__":
    asyncio.run(main())