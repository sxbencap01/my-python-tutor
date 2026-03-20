import streamlit as st
from code_analyzer import CodeAnalyzer
from llm_service import LLMService
from knowledge_manager import KnowledgeManager
from prompts import SYSTEM_PROMPT, KNOWLEDGE_PANEL_PROMPT
import json

# Page Configuration
st.set_page_config(
    page_title="Python 学习助手 - 引导式教学",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to mimic Coze style (simplified)
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stChatFloatingInputContainer {
        bottom: 20px;
    }
    .panel-container {
        border-radius: 10px;
        background-color: white;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

if "code" not in st.session_state:
    st.session_state.code = "print('Hello, Python Learner!')"

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "knowledge_summary" not in st.session_state:
    st.session_state.knowledge_summary = "### 📚 准备开始\n\n欢迎来到 Python 引导式学习。请在中间栏和我打个招呼吧！"

# Services
@st.cache_resource
def get_llm_service():
    return LLMService()

@st.cache_resource
def get_analyzer():
    return CodeAnalyzer()

@st.cache_resource
def get_knowledge_manager():
    return KnowledgeManager()

llm_service = get_llm_service()
analyzer = get_analyzer()
km = get_knowledge_manager()

# Sidebar for configuration
with st.sidebar:
    st.title("⚙️ 设置")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Enter your Gemini API Key")
    model_name = st.selectbox("Model", ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"])
    
    if api_key:
        import google.generativeai as genai
        llm_service.api_key = api_key
        llm_service.model_name = model_name
        genai.configure(api_key=api_key)
        llm_service.model = genai.GenerativeModel(model_name)

    st.divider()
    st.subheader("🎓 个人中心")
    st.write(km.get_summary())
    if st.button("重置学习进度"):
        km.data = {"current_topic": "Python 基础", "completed_topics": [], "concepts_learned": [], "progress": 0}
        km.save_data()
        st.rerun()

# 3-Column Layout
col_left, col_center, col_right = st.columns([1, 2, 1.5])

# LEFT: Knowledge & Instructions Panel
with col_left:
    st.subheader("📋 知识面板")
    st.markdown(st.session_state.knowledge_summary)
    
    # Progress tracker
    progress = st.progress(km.data.get("progress", 0))
    st.caption(f"当前进度: {km.data.get('progress', 0)}%")

# CENTER: Main Chat Panel
with col_center:
    st.subheader("💬 导师对话")
    
    # Display chat history
    chat_container = st.container(height=500)
    for message in st.session_state.messages:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("向导师提问或展示你的代码思路..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"):
            st.markdown(prompt)

        # Get response from LLM
        with chat_container.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
            
            for chunk in llm_service.chat_completion(messages):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        # Proactively update the knowledge panel in the background (mocking background task)
        # In a real app, this could be a separate call to the LLM
        # st.session_state.knowledge_summary = "Updating..." 

# RIGHT: Code Editor & Analysis Panel
with col_right:
    st.subheader("💻 代码沙盒")
    
    # Simple code editor using text_area (can be upgraded to streamlit-code-editor)
    code = st.text_area("在下方编写 Python 代码", value=st.session_state.code, height=300)
    st.session_state.code = code
    
    col_btns = st.columns(2)
    run_btn = col_btns[0].button("▶️ 运行代码", use_container_width=True)
    analyze_btn = col_btns[1].button("🔍 分析代码", use_container_width=True)

    if run_btn:
        with st.spinner("正在运行..."):
            output, error = analyzer.run_code(code)
            
            st.write("---")
            if error:
                st.error(f"❌ 运行错误:\n{error}")
            else:
                st.success("✅ 运行成功:")
                st.code(output if output else "[无输出]")

    if analyze_btn:
        with st.spinner("深度分析中..."):
            analysis = analyzer.analyze_structure(code)
            st.write("---")
            st.info("🤖 代码结构分析:")
            
            if "error" in analysis:
                st.error(analysis["error"])
            else:
                # Display structural information
                st.write(f"- **循环结构**: {'有' if analysis['has_loops'] else '无'}")
                st.write(f"- **函数定义**: {'有' if analysis['has_functions'] else '无'}")
                st.write(f"- **类定义**: {'有' if analysis['has_classes'] else '无'}")
                st.write(f"- **导入模块**: {', '.join(analysis['imports']) if analysis['imports'] else '无'}")
                st.write(f"- **变量数**: {analysis['variable_count']}")
                st.write(f"- **注释数**: {analysis['comments_count']}")

                # Ask the mentor to analyze the specific code
                # Add a hidden message to get specific code feedback
                analysis_prompt = f"请分析我这段代码的质量和逻辑，并给我一些改进建议，但不要直接给我最终代码：\n\n```python\n{code}\n```"
                st.session_state.messages.append({"role": "user", "content": analysis_prompt})
                st.rerun()

# Footer
st.divider()
st.caption("由 Python 引导式学习智能体提供支持 | 关注过程，而非仅仅是结果。")
