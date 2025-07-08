# langchain_helper.py
"""
This module provides utility functions to extract and analyze YouTube video transcripts
using LangChain, FAISS, and OpenAI's language models.
"""
from langchain_community.document_loaders import YoutubeLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain, RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from youtube_transcript_api._errors import NoTranscriptFound

load_dotenv()
embeddings = OpenAIEmbeddings()


def create_db_from_youtube_video_url(video_url: str):
    """
    Loads and processes the transcript of a YouTube video into a vector database (FAISS).

    Args:
        video_url (str): The URL of the YouTube video.

    Returns:
        tuple: A tuple containing the FAISS vector store and the full transcript text.

    Raises:
        RuntimeError: If a transcript cannot be found in the specified languages.
    """
    try:
        loader = YoutubeLoader.from_youtube_url(video_url, language=["en", "tr"])
        transcript = loader.load()
    except NoTranscriptFound as e:
        raise RuntimeError(
            f"Transcript not found for the video. Available languages may not include 'en'. "
            f"Try a different video or support auto-translation.\n\nDetails: {str(e)}"
        )

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(transcript)

    db = FAISS.from_documents(docs, embeddings)
    full_transcript = " ".join([doc.page_content for doc in docs])

    return db, full_transcript

def get_video_summary(transcript_text: str):
    """
    Generates a detailed summary of the YouTube transcript using GPT-4.

    Args:
        transcript_text (str): The full transcript text.

    Returns:
        str: A detailed summary of the video content.
    """
    llm = ChatOpenAI(model_name="gpt-4", temperature=0.3)
    prompt = PromptTemplate(
        input_variables=["transcript"],
        template="""
        Summarize the following YouTube video transcript into a detailed summary.
        Highlight key points, topics discussed, and major conclusions:

        Transcript:
        {transcript}
        """,
    )
    chain = prompt | llm
    return chain.invoke({"transcript": transcript_text}).content

def get_chapters_from_transcript(transcript_text: str):
    """
    Segments the transcript into structured chapters with titles and brief descriptions.

    Args:
        transcript_text (str): The full transcript text.

    Returns:
        str: Structured chapter breakdown.
    """
    llm = ChatOpenAI(model_name="gpt-4", temperature=0.3)
    prompt = PromptTemplate(
        input_variables=["transcript"],
        template="""
        Divide this YouTube video transcript into a list of chapters with titles.
        Each chapter should be a short title and a brief description.

        Transcript:
        {transcript}
        """,
    )
    chain = prompt | llm
    return chain.invoke({"transcript": transcript_text}).content

def get_response_from_query(db, query, k=4):
    """
    Answers user questions by retrieving relevant transcript chunks and using GPT-4.

    Args:
        db (FAISS): The vector store built from the transcript.
        query (str): The user's question.
        k (int, optional): Number of relevant chunks to retrieve. Defaults to 4.

    Returns:
        tuple: A tuple of the generated response string and list of source documents.
    """
    retriever = db.as_retriever(search_kwargs={"k": k})
    llm = ChatOpenAI(model_name="gpt-4", temperature=0.3)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
    )

    result = qa_chain.invoke({"query": query})
    return result["result"], result["source_documents"]