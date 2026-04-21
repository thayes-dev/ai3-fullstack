import streamlit as st

st.title("Execution Model Demo")

st.write("This line runs every time.")

name = st.text_input("Enter your name:")
st.write(f"Hello, {name}!")

count = 0
count += 1
st.write(f"Count: {count}")