import streamlit as st

st.set_page_config(page_title="Stableman", page_icon="🐴")

st.title("🐴 Stableman")
st.write("Welcome to the Stableman Streamlit app!")

st.header("About")
st.write("""
This is a basic Streamlit application for the Stableman project.
Streamlit is an open-source Python library that makes it easy to create 
beautiful web apps for data science and machine learning.
""")

st.header("Getting Started")
st.write("This app demonstrates some basic Streamlit features:")

# Simple text input
name = st.text_input("What's your name?", "")
if name:
    st.write(f"Hello, {name}! 👋")

# Slider example
value = st.slider("Select a value:", 0, 100, 25)
st.write(f"Selected value: {value}")

# Selectbox example
option = st.selectbox(
    "Choose an option:",
    ["Option 1", "Option 2", "Option 3"]
)
st.write(f"You selected: {option}")

# Button example
if st.button("Click me!"):
    st.balloons()
    st.success("Button clicked! 🎉")

st.divider()

st.info("💡 To learn more about Streamlit, visit [streamlit.io](https://streamlit.io)")
