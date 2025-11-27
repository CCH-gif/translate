# translate
# 📂 智能文件翻译助手

一个基于LangChain和通义千问大模型的智能文件处理系统，支持文件读取、多语言翻译和智能保存功能。

## ✨ 功能特性

- **📄 多格式文件读取**: 支持 `.txt`, `.pdf`, `.docx` 格式文件
- **🌍 智能翻译**: 集成通义千问大模型，支持多种语言互译
- **💾 智能保存**: 自动创建文件夹并保存处理结果
- **🤖 Agent驱动**: 基于LangChain的智能Agent协调工具调用
- **🎨 图形界面**: 提供Streamlit Web界面和命令行界面

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 阿里云 DashScope API Key

### 安装依赖

pip install -r requirements.txt### 配置API Key

1. 获取阿里云DashScope API Key
2. 在代码中配置API Key：
   - 命令行版本：编辑 `translation.py` 第218行
   - Web版本：在侧边栏输入API Key

### 运行应用

#### 命令行版本
python translation.py#### Web界面版本
streamlit run app.py## 📖 使用指南

### 基本指令格式
