"""Streamlit entry point for the VideoLingo web UI.

The UI implementation remains in ``st.py``; this compatibility entry point
lets launchers consistently start it as ``webui.py``.
"""

from st import main


if __name__ == "__main__":
    main()
