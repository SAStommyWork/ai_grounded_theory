from docx import Document
import gradio as gr
from openai import OpenAI
import subprocess
import os
import logging
#from graphviz import Digraph
logging.basicConfig(level=logging.DEBUG)

def linkopenai(apikey):
    try:
        client = OpenAI(
            api_key=apikey,
        )
        return client
    except Exception as e:
        print(e)
        return None  
    
grounded_theory_tree_path = "./tmp/grounded_theory_tree"
#grounded_theory_tree_path = "./public/grounded_theory_tree"
#function_graph_path = "/tmp/functiongraph.py"

def generategraph(code_string):
    if not os.path.exists("./public"):
        os.makedirs("./public")
    if os.path.exists(f"{grounded_theory_tree_path}.png"):
        os.remove(f"{grounded_theory_tree_path}.png")
    
    # 在 /tmp/ 目錄中創建 functiongraph.py 文件
    #with open(function_graph_path, "w", encoding="utf-8") as f:
    #    f.write(code_string)
    
    # 執行 /tmp/functiongraph.py，捕獲執行結果
    #result = subprocess.run(["python", function_graph_path], capture_output=True, text=True)
    
    # 执行 Python 文件并捕获输出
    #subprocess.run(["python", "functiongraph.py"], capture_output=True, text=True)
    result = subprocess.run(["python", "-c", code_string], capture_output=True, text=True)
    logging.error("生成圖像的輸出：", result.stdout)
    logging.error("生成圖像的錯誤：", result.stderr)
    
    logging.error(f"檢查圖片是否存在：{grounded_theory_tree_path}")
    #if not os.path.exists("grounded_theory_tree.png"):
        #raise FileNotFoundError(f"{grounded_theory_tree_path}文件未生成，check your code。")

# 读取 docx 文件的函数
def load_docx_data(files):
    content = []
    for file in files:
        doc = Document(file)
        # 获取每个文档的段落并添加到内容列表
        content.extend([para.text for para in doc.paragraphs if para.text])  # 只添加非空段落
        content.append("")  # 添加一个空字符串作为段落分隔符
    return content

lang = "且所有回應用使用英文回答"

# AI 进行扎根理论三层编码的函数
def grounded_theory_analysis(client, content):
    global open_coding, axial_coding, selective_coding
    dialog_history = [{"role": "system", "content": f"你是紮根理論的研究專家, 你也能夠截取資料文本原文(句子不會進行任何修改, 句子會與資料文本完全相同)作為根據{lang},你亦是一個python工程師,你不會寫出有錯誤的代碼"}]
    
    open_prompt = f"请對前面由{len(content)}段组成的文本進行開放式編碼，并列出主要概念後面用()加上對應資料作為根據"
    for i, part in enumerate(content):
        if i == len(content) - 1:
            dialog_history.append({"role": "user", "content": open_prompt})
        else:
            dialog_history.append({"role": "user", "content": f"你需要閱讀内容，即將接受在{len(content)}中的第{i + 1}部分\n\n{part}"})
        
    # 调用 API
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=dialog_history
    )
    
    open_coding =  response.choices[0].message.content
    dialog_history.append({"role": "assistant", "content": open_coding})
    
    
    # 主轴编码
    axial_prompt = f"根據已完成開放式編碼结果，進行主軸編碼，建立類别之間的聯繫並後面用()加上對應資料開放式編碼作為根據：\n\n{open_coding}"
    dialog_history.append({"role": "user", "content": axial_prompt})
    axial_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=dialog_history
    )
    axial_coding = axial_response.choices[0].message.content
    dialog_history.append({"role": "assistant", "content": axial_coding})
    
    # 选择性编码
    selective_prompt = f"根據已完成主軸編碼结果，進行選擇性編碼，提煉核心類别并形成理論框架後面用()加上對應資料主軸編碼作為根據：\n\n{axial_coding}"
    dialog_history.append({"role": "user", "content": selective_prompt})
    selective_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=dialog_history
    )
    selective_coding = selective_response.choices[0].message.content
    dialog_history.append({"role": "assistant", "content": selective_coding})
    
    # 汇总结果
    result = f"**Open coding：**\n{open_coding}\n\n"
    result += f"**Axial coding：**\n{axial_coding}\n\n"
    result += f"**Selective coding：**\n{selective_coding}"
    
    return result

def getgraphcode(client, result, level_num, node_num_1, node_num_2, node_num_3):
    code_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"""根據以下資料:\n{result}\n生成用畫出紮根理論{level_num}層樹狀圖, 第一層的節點數為一定在{node_num_1}以內, 第二層的節點數一定在{node_num_2}以內, 第三層的節點數一定在{node_num_3}以內及圖片以grounded_theory_tree.png儲存的python程式碼, 
                   內容用英文寫, 其中程式碼依照情況必定包括以下13行:\n
                   dot = Digraph('G', format='png', directory='/tmp')\n
                   dot.attr("graph", fontname='Times New Roman', fontweight="bold")\n
                   dot.attr("node", fontname='Times New Roman', fontweight="bold")\n
                   dot.attr("edge", fontname='Times New Roman', fontweight="bold")\n
                   # 添加层名标记节点(以下為3層樹狀圖使用樣式)\n
                   dot.node("OpenCodingLabel", "Open coding", shape="plaintext", fontname='Times New Roman', fontweight="bold")\n
                   dot.node("AxialCodingLabel", "Axial coding", shape="plaintext", fontname='Times New Roman', fontweight="bold")\n
                   dot.node("SelectiveCodingLabel", "Selective coding", shape="plaintext", fontname='Times New Roman', fontweight="bold")\n
                   注: 2層樹狀圖樣式與3層不同(只有3層中的其中2行)且名字根據關係自行命名而不是"Open coding", "Axial coding", "Selective coding"\n
                   # 连接层名标记到每一层的所有节点(按層數加入)\n
                   for node_id in open_coding_nodes:\n
                        dot.edge("OpenCodingLabel", node_id, style="dashed")\n
                   for node_id in axial_coding_nodes:\n
                        dot.edge("AxialCodingLabel", node_id, style="dashed")\n
                   for node_id in selective_coding_nodes:\n
                        dot.edge("SelectiveCodingLabel", node_id, style="dashed")\n
                   dot.render(filename=grounded_theory_tree_path, format='png')\n
                   只需要回傳python程式碼, 不需要任何描述"""}]
    )
    code_string = code_response.choices[0].message.content
    code_string = code_string.replace("```python", "").replace("```", "")
     # 删除 import 之前的所有内容
    import_index = code_string.find('import')
    if import_index != -1:
        code_string = code_string[import_index:]
    code_string = code_string.replace("import Digraph", "from graphviz import Digraph")
    return code_string

# 动态处理输入的函数
def main(apikey, files, level_num, node_num_1, node_num_2, node_num_3):
    print(files)
    if apikey == "":
        return "<h1 style='color:red;'>Please write your OpenAI key</h1>", None
    elif files is None:
        return "<h1 style='color:red;'>Please upload at least one .docx file.</h1>", None
    else:
        client = linkopenai(apikey)
        if client == "":
            return "<h1 style='color:red;'>wrong apikey, please check your openai key</h1>", None
        content = load_docx_data(files)
        analysis_result = grounded_theory_analysis(client, content)
        generategraph(getgraphcode(client, analysis_result, level_num, node_num_1, node_num_2, node_num_3))
        return analysis_result, f"{grounded_theory_tree_path}.png"

# 更新输入状态
def update_dynamic_inputs(level_num):
    return (
        gr.update(interactive=level_num >= 2, value=None if level_num < 2 else 5),  # 第二层输入框
        gr.update(interactive=level_num == 3, value=None if level_num < 3 else 5)  # 第三层输入框
    )

# 创建界面
with gr.Blocks() as iface:
    gr.Markdown("<h1 style='text-align: center;'>Grounded Theory Analyzer</h1>")
    gr.Markdown("Upload .docx files of up to 100,000 words, and use AI to automate the analysis of the grounded theory three-layer structure, and display the results and structure diagram for each layer")
    apikey = gr.Textbox(label="write your openAI key", type="password")
    with gr.Row():
        with gr.Column(scale=1):
            files_input = gr.File(label="upload .docx documents", file_count="multiple")
            level_num = gr.Dropdown(
                value=3,
                choices=[1, 2, 3],
                label="Select the number of levels for analysis"
            )
            
            node_num_1 = gr.Number(value=10, label="Enter the maximum number of nodes in the first level", precision=0)
            node_num_2 = gr.Number(value=5, label="Enter the maximum number of nodes in the second level", precision=0, interactive=True)
            node_num_3 = gr.Number(value=5, label="Enter the maximum number of nodes in the third level", precision=0, interactive=True)
            
            submit_btn = gr.Button("start analysis")
        
        with gr.Column(scale=2):
            result_output = gr.Markdown(
                value="<div style='height: 300px; border: 1px solid lightgrey; padding: 10px; border-radius: 5px;'>Results will be displayed here.</div>"
            )
            graph_output = gr.Image(type="pil")

    # 按钮点击处理
    submit_btn.click(
        fn=main,
        inputs=[apikey, files_input, level_num, node_num_1, node_num_2, node_num_3],
        outputs=[result_output, graph_output]
    )
    
    # 监听层次选择，动态更新输入框状态
    level_num.change(
        fn=update_dynamic_inputs,
        inputs=[level_num],
        outputs=[node_num_2, node_num_3]
    )

iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))