#!/bin/bash
# 关闭命令回显
set +v

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 激活 conda 环境
source activate videolingo

# 运行 Streamlit 应用
echo "初次启动会比较慢，请耐心等待..."
python -m streamlit run st.py

# 暂停脚本执行
read -p "按回车键继续..."