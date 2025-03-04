from math import exp
import gradio as gr
import asyncio
import json
from func import *
import time
from openai import AsyncOpenAI
from config import load_config, save_config, client
import os

# 加载工具配置
tools = open(r"AItools\tools.json", "r", encoding="utf-8").read()
tools = json.loads(tools)

class AILovelyMemUI:
    def __init__(self):
        self.messages = [
            {
                "role": "system", 
                "content": """作为Windows内存取证专家，你需要：
- 准确使用取证工具分析内存
- 只提取最关键的可疑信息
- 简明扼要地总结发现
- 直接给出重要结论

请保持回复简洁，直接突出重点内容。"""
            }]
        # 加载配置
        self.config = load_config()
        # 自动加载内存镜像信息
        try:
            with open('output/image_info.txt', 'r', encoding='utf-8') as f:
                info = f.read().split(',')
                self.mem_path = info[0]
                self.profile = info[1]
        except Exception as e:
            self.mem_path = "未找到内存镜像文件"
            self.profile = "未知"
        
    async def chat(self, message, history, output_box):
        """处理用户输入的聊天消息"""
        if message.lower() == 'q':
            yield [[message, "再见！"]], "", output_box
            return
        if message.lower() == 'clean':
            self.messages = [self.messages[0]]
            yield [[message, "对话已清空"]], "", output_box
            return
            
        self.messages.append({"role": "user", "content": message})
        history = history or []
        history.append([message, "🤔命令执行中..."])  # 添加思考中的提示
        yield history, "", output_box
        
        try:
            # 发送消息给AI
            response = await client.chat.completions.create(
                model=self.config["model"],
                messages=self.messages,
                tool_choice="auto",
                parallel_tool_calls=True,
                tools=tools,
                temperature=0.7
            )
            
            # 添加错误处理和空值检查
            if not response.choices:
                raise Exception("API返回的响应中没有choices")
                
            assistant_message = response.choices[0].message
            
            # 处理工具调用
            if assistant_message.tool_calls:
                self.messages.append(assistant_message)
                command_results = []
                
                for tool_call in assistant_message.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    func = globals().get(tool_call.function.name)
                    try:
                        # 显示执行状态和命令内容
                        command_text = f"""执行命令: {tool_call.function.name}
参数:
{json.dumps(args, indent=2, ensure_ascii=False)}
{'='*50}"""
                        status_text = "⚡ 正在执行命令"
                        history[-1][1] = "⚡ 正在执行命令"
                        yield history, "", output_box + "\n" + command_text
                        
                        
                        try:
                            for key, value in args.items():
                                print(f"[*] {key}: {value}")
                            result = await func(**args)
                        except Exception as e:
                            print(f"[-] 执行失败：{str(e)}")
                            
                        command_result = f"""{command_text}
结果:
{result}
{'='*50}"""
                        command_results.append(command_result)
                        # 更新命令执行结果
                        yield history, "", output_box + "\n" + "\n".join(command_results)

                    except Exception as e:
                        result = f"工具执行失败: {str(e)}"
                        command_result = f"""命令执行失败: {tool_call.function.name}
{'='*50}
{result}
{'='*50}"""
                        command_results.append(command_result)
                        yield history, "", output_box + "\n" + "\n".join(command_results)

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

                history[-1][1] = "🔍分析结果中..."
                yield history, "", output_box + "\n" + "\n".join(command_results)

                # 获取最终响应
                final_response = await client.chat.completions.create(
                    model=self.config["model"],
                    messages=self.messages,
                    stream=True
                )
                collected_messages = []
                command_output = output_box + "\n" + "\n".join(command_results)  # 保存命令执行结果
                async for chunk in final_response:
                    try:
                        if (chunk.choices and 
                            len(chunk.choices) > 0 and 
                            hasattr(chunk.choices[0], 'delta') and 
                            hasattr(chunk.choices[0].delta, 'content') and 
                            chunk.choices[0].delta.content):
                            collected_messages.append(chunk.choices[0].delta.content)
                            history[-1][1] = "".join(collected_messages)
                            yield history, "", command_output  # 使用保存的命令执行结果
                    except (AttributeError, IndexError) as e:
                        continue
                
                final_message = "".join(collected_messages)
                self.messages.append({"role": "assistant", "content": final_message})
                
            else:
                # 没有工具调用，直接流式输出AI回复
                final_response = await client.chat.completions.create(
                    model=self.config["model"],
                    messages=self.messages,
                    stream=True
                )
                collected_messages = []
                async for chunk in final_response:
                    try:
                        if (chunk.choices and 
                            len(chunk.choices) > 0 and 
                            hasattr(chunk.choices[0], 'delta') and 
                            hasattr(chunk.choices[0].delta, 'content') and 
                            chunk.choices[0].delta.content):
                            collected_messages.append(chunk.choices[0].delta.content)
                            history[-1][1] = "".join(collected_messages)
                            yield history, "", output_box  # 没有命令执行时保持原有输出
                    except (AttributeError, IndexError) as e:
                        continue
                
                final_message = "".join(collected_messages)
                self.messages.append({"role": "assistant", "content": final_message})
                
        except Exception as e:
            error_msg = f"发生错误: {str(e)}"
            history[-1][1] = error_msg
            yield history, "", output_box + "\n" + error_msg

    def reload_image_info(self):
        """重新读取内存镜像信息"""
        try:
            with open('output/image_info.txt', 'r', encoding='utf-8') as f:
                info = f.read().split(',')
                self.mem_path = info[0]
                self.profile = info[1]
                return f"""
                **内存镜像路径**: {self.mem_path}  
                **系统版本**: {self.profile}
                """
        except Exception as e:
            self.mem_path = "未找到内存镜像文件"
            self.profile = "未知"
            return f"""
            **内存镜像路径**: {self.mem_path}  
            **系统版本**: {self.profile}
            """

    def save_settings(self, api_key, base_url, model):
        """保存设置"""
        self.config["api_key"] = api_key
        self.config["base_url"] = base_url
        self.config["model"] = model
        save_config(self.config)
        # 更新客户端配置
        global client
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        return "配置已保存"

    def create_ui(self):
        """创建Gradio界面"""
        with gr.Blocks(title="AILovelyMem", theme=gr.themes.Soft(), css="""
            * {
                font-family: "Microsoft YaHei", sans-serif !important;
            }
            .status-container {
                min-height: 40px;
                margin-bottom: 10px;
            }
            .executing {
                color: #2196F3;
                font-weight: bold;
                padding: 12px 16px;
                border-radius: 8px;
                border-left: 4px solid #2196F3;
                background-color: #E3F2FD;
                margin: 10px 0;
                box-shadow: 0 2px 4px rgba(33, 150, 243, 0.1);
                animation: pulse 2s infinite;
                display: block;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            /* 强制控制TextArea高度 */
            #component-4 textarea.svelte-173056l {
                height: 150px !important;
                min-height: 150px !important;
                max-height: 150px !important;
            }
            """) as interface:
            
            gr.Markdown("# 🔍 AILovelyMem")
            
            # 添加设置区域
            with gr.Accordion("⚙️ 设置", open=False):
                with gr.Row():
                    api_key = gr.Textbox(
                        label="API Key",
                        value=self.config["api_key"],
                        type="password"
                    )
                    base_url = gr.Textbox(
                        label="Base URL",
                        value=self.config["base_url"]
                    )
                    model = gr.Textbox(
                        label="Model",
                        value=self.config["model"]
                    )
                save_btn = gr.Button("💾 保存设置")
            
            # 上方区域：命令执行结果
            with gr.Column():
                output_box = gr.TextArea(
                    label="命令执行结果", 
                    interactive=False,
                    autoscroll=True,
                    show_copy_button=True
                )
            
            gr.Markdown("---")  # 分隔线
            
            # 中间区域：对话界面（铺满）
            chatbot = gr.Chatbot(
                label="对话区域", 
                height=600,
                show_copy_button=True,
                elem_classes="chatbot"
            )
            with gr.Row():
                msg = gr.Textbox(
                    label="输入问题",
                    placeholder="在这里输入你的问题...",
                    show_label=False,
                    scale=9,
                    container=False
                )
                submit = gr.Button(
                    "发送",
                    scale=1,
                    variant="primary",
                    min_width=100
                )
            
            with gr.Row():
                clear = gr.Button(
                    "🗑️ 清空对话",
                    scale=1,
                    variant="secondary",
                    min_width=100
                )
                reload_btn = gr.Button(
                    "🔄 重新读取镜像",
                    scale=1,
                    variant="secondary",
                    min_width=100
                )

            gr.Markdown("---")  # 分隔线
            
            # 底部区域：内存镜像信息
            with gr.Accordion("📄 内存镜像信息", open=False) as info_accordion:
                image_info = gr.Markdown(f"""
                **内存镜像路径**: {self.mem_path}  
                **系统版本**: {self.profile}
                """)
            
            # 事件处理
            def clear_inputs():
                return None, "", ""
            
            submit.click(
                fn=self.chat,
                inputs=[msg, chatbot, output_box],
                outputs=[chatbot, msg, output_box],
                show_progress=True
            )
            
            # 添加回车键支持
            msg.submit(
                fn=self.chat,
                inputs=[msg, chatbot, output_box],
                outputs=[chatbot, msg, output_box],
                show_progress=True
            )
            
            clear.click(
                fn=clear_inputs,
                inputs=[],
                outputs=[chatbot, output_box, msg]
            )
            
            # 添加重新读取镜像按钮事件
            reload_btn.click(
                fn=self.reload_image_info,
                outputs=[image_info],
                show_progress=True
            )
            
            save_btn.click(
                fn=self.save_settings,
                inputs=[api_key, base_url, model],
                outputs=[gr.Textbox(label="状态")],
                show_progress=True
            )

        return interface

def main():
    ui = AILovelyMemUI()
    interface = ui.create_ui()
    export_url = "http://127.0.0.1:7860"
    subprocess.Popen(["explorer", export_url])
    interface.launch(
        share=False, 
        server_name="127.0.0.1",
        height=700,  # 设置整体界面高度
        show_api=False
    )
    # 打开浏览器
    

if __name__ == "__main__":
    main()
