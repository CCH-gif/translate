import streamlit as st
import os
from demo01 import init_agent_service, run_agent_logic

# --- 页面配置 ---
st.set_page_config(
    page_title="智能文件翻译助手",
    page_icon="📂",
    layout="centered"
)

# --- 自定义样式 ---
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
    }
    .stChatInput {
        position: fixed;
        bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏：设置 ---
with st.sidebar:
    st.header("⚙️ 配置")
    st.markdown("请输入您的阿里云 DashScope API Key:")
    
   
    default_key = os.environ.get("DASHSCOPE_API_KEY", "")
    api_key = st.text_input("API Key", value=default_key, type="password")
    
    if st.button("重置/初始化 Agent"):
        if api_key:
            try:
                st.session_state.agent = init_agent_service(api_key)
                st.session_state.messages = [] 
                st.session_state.agent_ready = True
                st.success("Agent 初始化成功！")
            except Exception as e:
                st.error(f"初始化失败: {e}")
        else:
            st.warning("请先输入 API Key")

    st.divider()
    st.markdown("""
    **💡 使用提示:**
    1. 确保要处理的文件路径正确（建议直接右键文件复制路径）。
    2. 可以在指令中包含读取、翻译、保存的完整流程。
    """)
    
    if st.button("🗑️ 清空聊天记录"):
        st.session_state.messages = []
        st.rerun()

# --- 初始化 Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "你好！我是你的智能文件助手。请告诉我你想处理哪个文件？（请提供文件的完整路径）"}]

if "agent_ready" not in st.session_state:
    st.session_state.agent_ready = False

# --- 主界面标题 ---
st.title("📂 智能文件翻译助手")
st.caption("基于 LangChain + Qwen-Plus | 支持 PDF/Word/TXT 读取与翻译")

# --- 检查 Agent 状态 ---
if not st.session_state.agent_ready:
    st.info("👈 请先在左侧侧边栏输入 API Key 并点击初始化。")
else:
    # --- 渲染聊天历史 ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- 处理用户输入 ---
    if prompt := st.chat_input("输入指令，例如：读取桌面的 test.txt，翻译成英文并保存..."):
        # 1. 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. 调用后端 Agent
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("正在思考与处理文件... (这可能需要几十秒)"):
                try:
                    # 获取 Agent 实例
                    agent = st.session_state.agent
                    # 运行逻辑
                    response = run_agent_logic(agent, prompt)
                    
                    # 显示结果
                    message_placeholder.markdown(response)
                    
                    # 保存助手回复到历史
                    st.session_state.messages.append({"role": "assistant", "content": response})
                
                except Exception as e:
                    error_msg = f"发生系统错误: {str(e)}"
                    message_placeholder.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})