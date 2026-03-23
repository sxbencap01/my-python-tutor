import streamlit as st
import json
import os
import time
from llm_service import LLMService
from code_analyzer import CodeAnalyzer
from knowledge_manager import KnowledgeManager
from prompts import SYSTEM_PROMPT, KNOWLEDGE_PANEL_PROMPT
from docx import Document

# 页面配置
st.set_page_config(page_title="AI 导师系统", page_icon="🎓", layout="wide")

# 初始化服务 (单例模式)
@st.cache_resource
def init_services():
    api_key = os.environ.get("API_KEY", "sk-fcpopflkqdeekzoqqneycwcmanrcznzrimnggvcmanyqedry")
    model = os.environ.get("LLM_MODEL", "Qwen/Qwen3-235B-A22B-Instruct-2507")
    return LLMService(api_key=api_key, model=model), CodeAnalyzer(), KnowledgeManager()

llm_service, analyzer, km = init_services()

# 初始化 Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_content" not in st.session_state:
    st.session_state.file_content = ""

# 侧边栏：知识状态与文件上传
with st.sidebar:
    st.title("🎓 学习看板")
    
    # 知识摘要
    st.markdown(km.get_summary())
    
    if st.button("重置学习状态"):
        km.data = {"current_topic": "待开始", "completed_topics": [], "concepts_learned": []}
        km.save_data()
        st.rerun()

    st.divider()
    
    # 文件上传
    uploaded_file = st.file_uploader("上传 Python/Docx 文件辅助学习", type=['py', 'txt', 'docx'])
    if uploaded_file:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext in ['.py', '.txt']:
            st.session_state.file_content = uploaded_file.read().decode('utf-8', errors='ignore')
        elif ext == '.docx':
            doc = Document(uploaded_file)
            st.session_state.file_content = '\n'.join([p.text for p in doc.paragraphs])
        st.success(f"已加载: {uploaded_file.name}")
        if st.session_state.file_content:
            with st.expander("查看文件内容"):
                st.code(st.session_state.file_content, language='python' if ext == '.py' else None)

# 主界面：聊天窗口
st.title("🤖 AI 编程导师")
st.caption("采用“三轮引导法”，先理解思想，后接触代码。")

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入
if prompt := st.chat_input("向导师提问..."):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 准备上下文
    context_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if st.session_state.file_content:
        context_messages.append({"role": "system", "content": f"当前分析的文件内容如下：\n{st.session_state.file_content}"})
    context_messages.extend(st.session_state.messages)

    # 生成回复
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        for chunk in llm_service.chat_completion(context_messages):
            full_response += chunk
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # 知识萃取逻辑 (异步/后续处理)
        try:
            history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
            extract_messages = [
                {"role": "system", "content": KNOWLEDGE_PANEL_PROMPT},
                {"role": "user", "content": f"分析以下对话并更新学习状态：\n{history_text}"}
            ]
            
            extraction = ""
            for c in llm_service.chat_completion(extract_messages):
                extraction += c
            
            clean_json = extraction.strip().replace('```json', '').replace('```', '').strip()
            update_data = json.loads(clean_json)
            
            if "learned_concepts" in update_data:
                km.data["concepts_learned"] = list(set(km.data["concepts_learned"] + update_data["learned_concepts"]))
            if "current_topic" in update_data:
                km.data["current_topic"] = update_data["current_topic"]
            km.save_data()
        except Exception as e:
            pass # 萃取失败不影响主流程

# 代码运行器 (下方固定区域)
st.divider()
st.subheader("💻 代码演练场")
code_to_run = st.text_area("在下方编写代码并运行验证：", height=150, placeholder="print('Hello World')")
if st.button("运行代码"):
    if code_to_run:
        output, error = analyzer.run_code(code_to_run)
        if output:
            st.code(output)
        if error:
            st.error(f"运行时错误: {error}")
    else:
        st.warning("请输入代码后再运行。")
