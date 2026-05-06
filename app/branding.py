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
        page_title="BrookWise",
        page_icon=".streamlit/static/favicon.png",
        layout="wide",
    )

    st.sidebar.image(".streamlit/static/logo.png", width=200)

    st.markdown("""
<style>
[data-testid="stChatMessage"] {
    border-radius: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.25);
}
[data-testid="stSidebar"] h1 {
    display: none;
}
[data-testid="stSidebar"] p {
    font-size: 1rem;
    color: #CAE9FF;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)
