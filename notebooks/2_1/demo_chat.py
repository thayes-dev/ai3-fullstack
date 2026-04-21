import streamlit as st

st.title("Chat Loop Demo")

# Part 1: Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Part 2: Display all previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Part 3: Handle new input
if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    reply = f"You said: {prompt}"
    with st.chat_message("assistant"):
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})