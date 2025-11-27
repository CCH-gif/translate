import os


from pypdf import PdfReader
from docx import Document as DocxDocument


from langchain_community.chat_models import ChatTongyi 
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool
from langchain.pydantic_v1 import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory


llm_instance = None


def get_llm(api_key):
    """
    初始化 LLM
    """
    global llm_instance
    if llm_instance is None:
        llm_instance = ChatTongyi(
            temperature=0.1, 
            model_name="qwen-plus", 
            dashscope_api_key=api_key,
        )
    return llm_instance


class ReadFileInput(BaseModel):
    file_path: str = Field(description="文件的完整本地路径，支持 .txt, .pdf, .docx 格式")

@tool("read_local_file", args_schema=ReadFileInput)
def read_local_file(file_path: str) -> str:
    """
    用于读取本地文件的内容。
    支持的文件格式：
    1. 纯文本 (.txt, .md, .py, .csv)
    2. Word 文档 (.docx)
    3. PDF 文档 (.pdf)
    """
   
    file_path = file_path.strip('"').strip("'")
    
    if not os.path.exists(file_path):
        return f"错误: 找不到文件 {file_path}"
    
    file_ext = os.path.splitext(file_path)[1].lower()
    content = ""

    try:
        # --- 情况 A: 处理 PDF ---
        if file_ext == '.pdf':
            reader = PdfReader(file_path)
            text_list = []
            for page in reader.pages:
                text_list.append(page.extract_text())
            content = "\n".join(text_list)
            
        # --- 情况 B: 处理 Word (.docx) ---
        elif file_ext == '.docx':
            doc = DocxDocument(file_path)
            # 提取每一个段落的文字并换行拼接
            content = "\n".join([para.text for para in doc.paragraphs])
            
        # --- 情况 C: 处理普通文本 (.txt, .md, etc.) ---
        else:
            
            try:
                with open(file_path, "r", encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding='gbk') as f:
                    content = f.read()

        # --- 长度检查 ---
        if not content.strip():
            return "警告: 文件内容为空，或者无法提取到文字（可能是扫描版图片PDF）。"
            
        if len(content) > 30000:
            return f"文件过长 ({len(content)}字符)，为了防止报错，截取前30000字符:\n{content[:30000]}..."
            
        return content

    except Exception as e:
        return f"读取文件时发生错误: {str(e)}"

# ===========================
# 1. 定义翻译工具 (核心功能)
# ===========================


class TranslationInput(BaseModel):
    text: str = Field(description="需要被翻译的原始文本内容")
    target_language: str = Field(description="目标语言，例如：中文、English、Japanese")

@tool("universal_translator", args_schema=TranslationInput)
def universal_translator(text: str, target_language: str) -> str:
    """
    这是一个万能翻译工具。
    当用户请求翻译文本时，必须先使用此工具获得翻译结果。
    """
    if llm_instance is None:
        return "错误: LLM 未初始化。"

    template = """
    你是一个专业翻译引擎。
    任务：将以下文本准确翻译成【{target}】。
    
    待翻译文本:
    {text}
    
    要求：
    1. 仅输出翻译后的最终内容。
    2. 不要包含任何解释性文字（如"翻译如下"）。
    """
    
    prompt = PromptTemplate(input_variables=["target", "text"], template=template)
    chain = prompt | llm_instance
    try:
        result = chain.invoke({"target": target_language, "text": text})
        return result.content
    except Exception as e:
        return f"翻译失败: {str(e)}"

# ===========================
# 2. 定义其他工具
# ===========================
class SaveToFolderInput(BaseModel):
    content: str = Field(description="要保存的文本内容")
    folder_name: str = Field(description="要创建或使用的文件夹名称")
    filename: str = Field(description="保存的文件名，需包含后缀")

@tool("save_to_folder", args_schema=SaveToFolderInput)
def save_to_folder(content: str, folder_name: str, filename: str) -> str:
    """
    文件保存工具。
    可以在桌面创建一个新的文件夹（如果不存在），并将内容保存到其中。
    """
    try:
       
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        
        # 拼接目标文件夹路径
        target_folder = os.path.join(desktop_path, folder_name)
        
        # 如果文件夹不存在，则创建
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
            
        # 拼接完整文件路径
        full_path = os.path.join(target_folder, filename)
        
        
        with open(full_path, "w", encoding='utf-8') as f:
            f.write(content)
            
        return f"成功: 文件已保存在文件夹【{folder_name}】中，路径: {full_path}"
    except Exception as e:
        return f"保存文件失败: {str(e)}"




# 初始化 Agent


def init_agent_service(api_key):
    if not api_key:
        raise ValueError("请提供 API Key")

    llm = get_llm(api_key)

    
    tools = [
         read_local_file,      
         universal_translator, 
         save_to_folder        
    ]
    
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True, 
        memory=memory,
        handle_parsing_errors=True,
        max_iterations=8, 
        agent_kwargs={
            "prefix": "你是一个全能的文件处理助手。你可以读取本地文件的内容，将其翻译，然后保存到指定的新文件夹中"
        }
    )
    return agent


    #  创建 Agent
    
    

def run_agent_logic(agent, user_input):
    try:
       
        response = agent.invoke({"input": user_input})
        return response['output']
    except Exception as e:
        return f"执行出错: {str(e)}"

if __name__ == "__main__":
    
    api_key = "" 
    
    if "sk-xxxx" in api_key:
        print("❌ 请先在代码中填入正确的 API Key")
        exit()

    try:
        agent = init_agent_service(api_key)
        print("\n" + "="*60)
        print("📁 智能文件翻译助手已就绪！")
        print("💡 您可以这样指令：")
        print("   '读取桌面的 test.txt 文件，翻译成英文，然后保存到桌面的 TranslationResult 文件夹里，文件名为 en_test.txt'")
        print("="*60 + "\n")
        
        while True:
            user_input = input("\n您：")
            if user_input.lower() in ['退出', 'exit', 'quit']:
                print("👋 再见！")
                break
            
            
            response = run_agent_logic(agent, user_input)
            print("助手：", response)
            
    except Exception as e:
        print(f"发生错误: {str(e)}")