import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq
from scraper import fetch_multiple_urls
from pdf_generator import convert_markdown_to_pdf
from main import SYSTEM_PROMPT
import history_manager

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
    .block-container {
        padding-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# Render Sidebar for Brochure History
with st.sidebar:
    st.markdown("## 📜 Brochure History")
    st.markdown("Click any past brochure to view and download.")
    
    history_records = history_manager.load_history()
    
    if history_records:
        for idx, item in enumerate(history_records):
            timestamp = item.get("timestamp", "Unknown time")
            title = item.get("title", "Brochure")
            
            button_label = f"🌐 {title}\n🕒 {timestamp}"
            if st.button(button_label, key=f"hist_{item['id']}"):
                st.session_state["brochure_text"] = item["markdown_content"]
                st.session_state["active_timestamp"] = timestamp
                st.session_state["active_title"] = title
                with st.spinner("Preparing PDF brochure..."):
                    try:
                        st.session_state["pdf_bytes"] = convert_markdown_to_pdf(item["markdown_content"])
                        st.session_state["pdf_error"] = None
                    except Exception as err:
                        st.session_state["pdf_bytes"] = None
                        st.session_state["pdf_error"] = str(err)
                st.rerun()

        st.markdown("---")
        if st.button("🗑️ Clear History"):
            history_manager.clear_history()
            st.session_state.pop("brochure_text", None)
            st.session_state.pop("pdf_bytes", None)
            st.session_state.pop("active_timestamp", None)
            st.session_state.pop("active_title", None)
            st.rerun()
    else:
        st.info("No brochure history found. Generate a brochure to save it here!")

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
                        
                        # Save entry into history
                        new_entry = history_manager.add_history_entry(urls, output_text, model_used=model_choice)
                        
                        st.session_state["brochure_text"] = output_text
                        st.session_state["active_timestamp"] = new_entry["timestamp"]
                        st.session_state["active_title"] = new_entry["title"]
                        
                        with st.spinner("Preparing PDF brochure..."):
                            try:
                                pdf_bytes = convert_markdown_to_pdf(output_text)
                                st.session_state["pdf_bytes"] = pdf_bytes
                                st.session_state["pdf_error"] = None
                            except Exception as pdf_err:
                                st.session_state["pdf_bytes"] = None
                                st.session_state["pdf_error"] = str(pdf_err)
                    except Exception as e:
                        st.error(f"An error occurred during generation: {str(e)}")

    # Display brochure and download controls if stored in session state
    if "brochure_text" in st.session_state and st.session_state["brochure_text"]:
        if st.session_state.get("active_timestamp"):
            st.caption(f"🕒 **Generated at:** {st.session_state['active_timestamp']}")
            
        # If not just generated on this run, render the stored markdown text
        if not generate_btn:
            st.markdown(st.session_state["brochure_text"])
        
        st.markdown("---")
        st.markdown("#### 📥 Download Brochure")
        
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            if st.session_state.get("pdf_bytes"):
                st.download_button(
                    label="📥 Download Brochure (.pdf)",
                    data=st.session_state["pdf_bytes"],
                    file_name="brochure.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            elif st.session_state.get("pdf_error"):
                st.error(f"Failed to generate PDF: {st.session_state['pdf_error']}")
        
        with dl_col2:
            st.download_button(
                label="📄 Download Brochure (.md)",
                data=st.session_state["brochure_text"],
                file_name="brochure.md",
                mime="text/markdown",
                use_container_width=True
            )
    elif not generate_btn:
        st.info("The generated brochure will stream here once you click 'Generate Brochure'.")
