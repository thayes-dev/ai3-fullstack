"""
branding.py -- Student-owned customization file.

Customize your app's appearance here. The instructor will NEVER modify this file.
Your changes survive all future git pulls.
"""
import streamlit as st


def apply_branding(config: dict) -> None:
    """Apply branding to the Streamlit app.

    Customize this function to personalize your app's appearance.

    Args:
        config: Dict from student_config.yaml with app_name, tagline, etc.
    """
    # IMPORTANT: st.set_page_config() MUST be the first st.* call in the app.
    # Do not add any st.write(), st.markdown(), etc. above this line.
    st.set_page_config(
        page_title=config.get("app_name", "Northbrook Q&A"),
        page_icon="📋",
        layout="wide",
    )

    # Logo -- uncomment and update path after adding your logo to .streamlit/static/
    # st.logo(".streamlit/static/logo.png")

    # Custom CSS -- add your styles here
    # st.markdown("""
    # <style>
    # /* Your custom CSS goes here */
    # </style>
    # """, unsafe_allow_html=True)
