from flask import Flask, request, jsonify, render_template, Response, stream_with_context, send_from_directory
from flask_cors import CORS
import os
import json
import logging
import socket
try:
    import qrcode
except ImportError:
    qrcode = None
from docx import Document
from llm_service import LLMService
from code_analyzer import CodeAnalyzer
from knowledge_manager import KnowledgeManager
from prompts import SYSTEM_PROMPT, KNOWLEDGE_PANEL_PROMPT


# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ======================================================
# 【关键配置区】 - 修改此处来调整您的 API Key
# ======================================================
# 优先从环境变量读取，如果不存在则使用硬编码（不建议在生产环境硬编码）
HARDCODED_API_KEY = os.environ.get("API_KEY", "sk-fcpopflkqdeekzoqqneycwcmanrcznzrimnggvcmanyqedry") 
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "Qwen/Qwen3-235B-A22B-Instruct-2507") 

# ======================================================

app = Flask(__name__)
CORS(app)

# 初始化服务
llm_service = LLMService(api_key=HARDCODED_API_KEY, model=DEFAULT_MODEL)
analyzer = CodeAnalyzer()
km = KnowledgeManager()

def get_host_ip():
    """获取本机局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def generate_qr_startup(port=5000):
    """启动时生成二维码"""
    if not qrcode:
        logger.warning("未安装 qrcode 库，跳过二维码生成。")
        return
        
    local_ip = get_host_ip()
    local_url = f"http://{local_ip}:{port}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(local_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 存放在 static 目录供前端显示或仅在本地生成
    qr_path = "server_qr.png"
    img.save(qr_path)
    
    print("\n" + "="*50)
    print("🚀 导师系统已启动！")
    print(f"🔗 本地访问地址: http://127.0.0.1:{port}")
    print(f"📱 局域网访问地址: {local_url}")
    print(f"📸 二维码已生成: {os.path.abspath(qr_path)}")
    print("="*50 + "\n")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    messages = data.get('messages', [])
    
    logger.info(f"收到聊天请求，消息条数: {len(messages)}")

    def generate():
        try:
            full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            has_output = False
            full_response = ""
            for chunk in llm_service.chat_completion(full_messages):
                if chunk:
                    has_output = True
                    full_response += chunk
                    yield chunk
            
            if not has_output:
                yield "导师正在思考中，请检查后端 API Key 配置。"
            else:
                # 对话结束后，触发知识萃取
                try:
                    # 提取最近 3 轮对话作为上下文，让萃取更准确
                    context_history = messages[-6:] if len(messages) > 6 else messages
                    context_text = "\n".join([f"{m['role']}: {m['content']}" for m in context_history])
                    context_text += f"\nassistant: {full_response}"

                    extract_messages = [
                        {"role": "system", "content": KNOWLEDGE_PANEL_PROMPT},
                        {"role": "user", "content": f"分析以下对话并更新学习状态：\n{context_text}"}
                    ]
                    
                    extraction = ""
                    for c in llm_service.chat_completion(extract_messages):
                        extraction += c
                    
                    try:
                        clean_json = extraction.strip().replace('```json', '').replace('```', '').strip()
                        update_data = json.loads(clean_json)
                        
                        # 1. 更新已掌握概念（由模型判定）
                        if "learned_concepts" in update_data:
                            km.data["concepts_learned"] = list(set(km.data["concepts_learned"] + update_data["learned_concepts"]))
                        
                        # 2. 更新当前话题
                        if "current_topic" in update_data:
                            km.data["current_topic"] = update_data["current_topic"]
                            
                        km.save_data()
                        logger.info(f"状态同步成功: Topic={km.data['current_topic']}")
                    except Exception as json_err:
                        logger.error(f"解析 JSON 失败: {str(json_err)}")
                except Exception as e:
                    logger.error(f"知识萃取失败: {str(e)}")
        except Exception as e:
            logger.error(f"生成回复时出错: {str(e)}")
            yield f"抱歉，发生了一个错误: {str(e)}"

    return Response(stream_with_context(generate()), mimetype='text/plain')

@app.route('/api/run_code', methods=['POST'])
def run_code():
    data = request.json
    code = data.get('code', '')
    output, error = analyzer.run_code(code)
    return jsonify({'output': output, 'error': error})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    content = ""
    
    try:
        if ext in ['.txt', '.py']:
            content = file.read().decode('utf-8', errors='ignore')
        elif ext in ['.docx']:
            doc = Document(file)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            content = '\n'.join(full_text)
        elif ext == '.doc':
            return jsonify({'error': '暂不支持旧版 .doc 格式，请另存为 .docx 后重试。'}), 400
        else:
            return jsonify({'error': f'不支持的文件类型: {ext}'}), 400
            
        return jsonify({'filename': filename, 'content': content})
    except Exception as e:
        logger.error(f"文件读取失败: {str(e)}")
        return jsonify({'error': f'文件读取失败: {str(e)}'}), 500

@app.route('/api/knowledge', methods=['GET'])
def get_knowledge():
    return jsonify(km.data)

@app.route('/api/reset_knowledge', methods=['POST'])
def reset_knowledge():
    km.data = {"current_topic": "待开始", "completed_topics": [], "concepts_learned": []}
    km.save_data()
    return jsonify(km.data)

@app.route('/server_qr.png')
def get_qr():
    # 确保在访问时如果文件不存在则尝试生成
    qr_path = os.path.join(os.getcwd(), 'server_qr.png')
    if not os.path.exists(qr_path):
        generate_qr_startup(port=5000)
    return send_from_directory(os.getcwd(), 'server_qr.png', cache_timeout=0)

if __name__ == '__main__':
    # 每次启动时强制初始化知识状态（如果需要）
    km.data = {"current_topic": "待开始", "completed_topics": [], "concepts_learned": []}
    km.save_data()
    
    # 适配魔搭空间 (ModelScope Space) 或其他环境
    port = int(os.environ.get("PORT", 7860))
    generate_qr_startup(port=port)
    logger.info(f"Flask 服务启动在 http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
