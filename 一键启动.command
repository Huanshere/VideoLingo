#!/bin/bash
cd "$(dirname "$0")"
export PATH="$PWD/runtime:$PATH"
echo "初次启动会比较慢，请耐心等待..."
"$PWD/runtime/python" -m streamlit run st.py
read -p "按任意键继续..."