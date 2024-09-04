#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
echo "初次启动会比较慢，请耐心等待..."
streamlit run st.py