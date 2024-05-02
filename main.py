import streamlit as st
import langchain_helper as lch
import textwrap
import os 

st.title("YouTube Video Summarizer")

with st.sidebar:
    with st.form(key='my_form'):
        youtube_url = st.sidebar.text_area(
            label="What is the YouTube video URL?",
            max_chars=50
            )
        query = st.sidebar.text_area(
            label="Ask me about the video?",
            max_chars=50,
            key="query"
            )
        "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
        submit_button = st.form_submit_button(label='Submit')

if query and youtube_url:
    if not os.environ['OPENAI_API_KEY']:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()
    else:
        db = lch.create_db_from_youtube_video_url(youtube_url)
        response, docs = lch.get_response_from_query(db, query)
        st.subheader("Answer:")
        st.text(textwrap.fill(response, width=85))