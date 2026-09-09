import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq
from scraper import fetch_multiple_urls
from main import SYSTEM_PROMPT

# Load environment variables
load_dotenv()

# Streamlit Page Configuration
st.set_page_config(
    page_title="Corporate Brochure Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a production-like UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #D1D5DB;
    }
    .stButton button {
        border-radius: 8px;
        background-color: #2563EB;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    .stButton button:hover {
        background-color: #1D4ED8;
    }
    /* Simple container styling */
    .block-container {
        padding-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# UI Layout
st.markdown('<p class="main-header">Corporate Brochure Generator</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Instantly transform any company website into a professional business brochure.</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.markdown("### 1. Website Links")
    st.markdown("Enter the URLs of the company website you want to analyze. Put each URL on a new line.")
    urls_input = st.text_area("URLs", height=150, placeholder="https://example.com\nhttps://example.com/about", label_visibility="collapsed")
    
    model_choice = st.selectbox(
        "Select Model", 
        ["qwen-2.5-32b", "llama-3.1-70b-versatile", "llama-3.1-8b-instant", "llama3-70b-8192", "mixtral-8x7b-32768", "qwen/qwen3.8-27b"],
        index=0,
        help="Select the AI model for generation. Choose your preferred or default model."
    )
    
    generate_btn = st.button("Generate Brochure")

with col2:
    st.markdown("### 2. Generated Brochure")
    
    if generate_btn:
        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        
        if not urls:
            st.warning("Please enter at least one URL.")
        elif not os.environ.get("GROQ_API_KEY"):
            st.error("GROQ_API_KEY is not set. Please add it to your .env file or environment.")
        else:
            with st.spinner("Scraping website content... This may take a moment."):
                scraped_content = fetch_multiple_urls(urls)
                
            if not scraped_content.strip():
                st.error("Could not extract any content from the provided URLs.")
            else:
                st.success("Website scraped successfully! Generating brochure...")
                
                # Stream the output directly to the UI
                with st.container():
                    def stream_generator():
                        client = Groq()
                        response = client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": f"Here is the scraped website content:\n\n{scraped_content}"}
                            ],
                            model=model_choice,
                            temperature=0.3,
                            max_tokens=4000,
                            stream=True,
                        )
                        for chunk in response:
                            if chunk.choices[0].delta.content is not None:
                                yield chunk.choices[0].delta.content
                    
                    try:
                        # st.write_stream renders the markdown progressively!
                        output_text = st.write_stream(stream_generator)
                        
                        st.download_button(
                            label="Download Brochure (.md)",
                            data=output_text,
                            file_name="brochure.md",
                            mime="text/markdown"
                        )
                    except Exception as e:
                        st.error(f"An error occurred during generation: {str(e)}")
    else:
        st.info("The generated brochure will stream here once you click 'Generate Brochure'.")
