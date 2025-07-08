# main.py
"""
Streamlit app for summarizing YouTube videos and querying their transcript using LangChain and OpenAI models.
"""
import re
from os import environ
import streamlit as st
from dotenv import load_dotenv
import utils.langchain_helper as lch

# Load environment variables from .env file
load_dotenv()

def format_chapters(raw_text: str) -> str:
    """
    Convert chapter headings to bold markdown format.

    Args:
        raw_text (str): Raw text containing chapters.

    Returns:
        str: Formatted markdown string.
    """
    pattern = r"Chapter (\d+):\s*(.+?)(?=Chapter \d+:|\Z)"
    matches = re.findall(pattern, raw_text, re.DOTALL)

    formatted = ""
    for number, content in matches:
        # Split the title from the description (first sentence assumed as title)
        parts = content.strip().split(None, 1)
        if len(parts) == 2:
            title, rest = parts
            formatted += f"**Chapter {number} - {title}:** {rest.strip()}\n\n"
        else:
            formatted += f"**Chapter {number}:** {content.strip()}\n\n"

    return formatted.strip()

# Set Streamlit app title
st.set_page_config(page_title="YouTube Summarizer", page_icon="📽️")

# Inject custom CSS for sticky footer
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        padding: 12px 24px;
        background: rgba(240, 240, 240, 0.9); /* light-ish background */
        color: #333;
        font-size: 0.9rem;
        text-align: center;
        border-top: 1px solid #ddd;
        z-index: 999;
    }
    
    @media (prefers-color-scheme: dark) {
        .footer {
            background: rgba(39, 39, 48, 0.9);
            color: #ffffff;
            border-top: 1px solid #444;
        }
    }

    html {
        padding-bottom: 60px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# App title
st.title("📽️ YouTube Video Summarizer")

# Sidebar input form
with st.sidebar:
    st.text_input("Enter YouTube video URL:", key="youtube_url")

    st.radio(
        "Choose an option:",
        ["Summarize", "Ask a question"],
        key="query_option"
    )

    if st.session_state.query_option == "Ask a question":
        st.text_area(
            "Ask something about the video:",
            max_chars=200,
            key="query"
        )

    submit_button = st.button("Submit")
    
    st.markdown("---")
    st.markdown(
        "[Get your OpenAI API key](https://platform.openai.com/account/api-keys)"
    )

# Main interaction logic
if submit_button:
    youtube_url = st.session_state.youtube_url
    query_option = st.session_state.query_option
    query = st.session_state.get("query", "")

    # Validate input first
    if not youtube_url:
        st.error("❌ Please enter a valid YouTube URL.")
        st.stop()

    if query_option == "Ask a question" and not query:
        st.warning("⚠️ Please enter a question to ask about the video.")
        st.stop()

    if not environ.get("OPENAI_API_KEY"):
        st.error("❌ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        st.stop()

    with st.spinner("Processing video... This may take a moment."):
        try:
            db, full_transcript = lch.create_db_from_youtube_video_url(youtube_url)
            
            # Summarization path
            if query_option == "Summarize":
                # Generate summary
                summary = lch.get_video_summary(full_transcript)
                st.subheader("🔄 Video Summary")
                st.markdown(summary)

                # Generate and display the chapters
                chapters = lch.get_chapters_from_transcript(full_transcript)
                st.subheader("📄 Chapters")
                with st.expander("See generated chapters"):
                    formatted_chapters = format_chapters(chapters)
                    st.markdown(formatted_chapters)
            
            # Q&A path
            elif query_option == "Ask a question":
                # Query the transcript
                st.subheader("🔍 Answer to your question")
                response, docs = lch.get_response_from_query(db, query)
                st.markdown(response)

                # Display retrieved context
                with st.expander("See retrieved transcript chunks"):
                    for i, doc in enumerate(docs, 1):
                        st.markdown(f"**Chunk {i}:** {doc.page_content[:300]}...")
        except Exception as e:
            st.error(f"❌ Failed to load or process video: {str(e)}")
            st.stop()

# Sticky footer
st.markdown(
    """
    <div class="footer">
        © 2025. All right reserved.
    </div>
    """,
    unsafe_allow_html=True
)
