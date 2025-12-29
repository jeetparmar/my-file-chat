import re
import base64
import pytesseract
import streamlit as st

from PIL import Image
from dotenv import load_dotenv

from config.settings import (
    APP_HEADER,
    APP_HEADER_CAPTION,
    APP_NAME,
    COMPANY_NAME,
    CURRENT_YEAR,
    FILE_TABS,
    FULL_ICON_URL,
    ICON_URL,
    VALID_ALL_TYPES,
    VALID_AUDIO_TYPES,
    VALID_IMAGE_TYPES,
)
from helper import Helper
from services.ai_service import AIService
from ui.formatters import UIFormatters

# --------------------------------------------------
# Init
# --------------------------------------------------
load_dotenv()

text = None
preview = None
helper = Helper()
ai_service = AIService()
formatters = UIFormatters()
uploaded_file = None
uploaded_file_name = None


# --------------------------------------------------
# Cache document loading
# --------------------------------------------------
@st.cache_data(show_spinner=False)
def loading_data_please_wait(uploaded_file):
    data = ""

    if uploaded_file.name.endswith(VALID_IMAGE_TYPES):
        data = pytesseract.image_to_string(Image.open(uploaded_file))

    elif uploaded_file.name.endswith(".txt"):
        data = uploaded_file.read().decode("utf-8")

    elif uploaded_file.name.endswith(".pdf"):
        data = helper.extract_text_and_display_pdf(uploaded_file)

    elif uploaded_file.name.endswith(".mp4"):
        data = helper.extract_text_from_uploaded_video(uploaded_file)

    elif uploaded_file.name.endswith(VALID_AUDIO_TYPES):
        data = helper.extract_text_from_uploaded_audio(uploaded_file)

    return data


def init_session_state():
    """Initialize session state variables"""
    if "response_array" not in st.session_state:
        st.session_state["response_array"] = []


def render_footer():
    footer = f"""
        <footer style="position: fixed; bottom: 0; right: 0; font-size: 13px; color: #888888;">
            &copy; {CURRENT_YEAR} {COMPANY_NAME}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        </footer>
        """
    st.markdown(footer, unsafe_allow_html=True)


def save_unsaved_after_login():
    if len(st.session_state["response_array"]) > 0:
        for result in st.session_state.response_array:
            helper.save_to_db(
                st.session_state.user["email"],
                uploaded_file_name,
                result["question"],
                re.sub(r"\s+", " ", result["answer"]).strip(),
            )
        st.session_state["response_array"] = []


def main():
    selected_keyword = None

    # --------------------------------------------------
    # Page Config
    # --------------------------------------------------
    st.set_page_config(page_title=APP_NAME, page_icon=ICON_URL)
    st.logo(FULL_ICON_URL, icon_image=FULL_ICON_URL, size="large")

    # Initialize session state
    init_session_state()

    # --------------------------------------------------
    # Sidebar
    # --------------------------------------------------
    with st.sidebar:

        if "user" not in st.session_state:
            if st.button("Login", use_container_width=True, icon=":material/login:"):
                helper.sign_in()
        else:
            helper.after_signed_in(st.session_state.user["email"])

        uploaded_file = st.file_uploader(
            "",
            type=VALID_ALL_TYPES,
            on_change=helper.reset_entries,
            label_visibility="collapsed",
        )

        if uploaded_file:
            uploaded_file_name = uploaded_file.name

            if uploaded_file_name.endswith(VALID_IMAGE_TYPES):
                preview = "image"
            elif uploaded_file_name.endswith(".txt"):
                preview = "text"
            elif uploaded_file_name.endswith(".pdf"):
                preview = "pdf"
                body = f"""
                    <iframe 
                        src="data:application/pdf;base64,{base64.b64encode(uploaded_file.read()).decode("utf-8")}" 
                        width="290" 
                        height="400">
                    </iframe>
                """
            elif uploaded_file_name.endswith(".mp4"):
                preview = "video"
            elif uploaded_file_name.endswith(VALID_AUDIO_TYPES):
                preview = "audio"

            query_head = helper.get_query_head(preview)
            text = loading_data_please_wait(uploaded_file)

            tab1, tab2, tab3, tab4 = st.tabs(FILE_TABS)

            # Preview
            with tab1:
                if preview == "image":
                    st.image(uploaded_file, use_container_width=True)
                elif preview == "pdf":
                    st.markdown(body, unsafe_allow_html=True)
                elif preview == "audio":
                    st.audio(uploaded_file)
                elif preview == "video":
                    st.video(uploaded_file)
                else:
                    st.html(f"<div style='height:400px;overflow:auto'>{text}</div>")

            # Cleaned text
            with tab2:
                generated = re.sub(r"\s+", " ", text).strip()
                st.html(f"<div style='height:400px;overflow:auto'>{generated}</div>")

            # Keywords
            with tab3:
                if "user" in st.session_state:
                    if st.button(
                        "Generate Keywords",
                        use_container_width=True,
                        icon=":material/tag:",
                    ):
                        count = st.slider("", 5, 100, 10, label_visibility="collapsed")
                        selection = st.pills(
                            "",
                            helper.generate_keywords(text, count),
                            label_visibility="collapsed",
                        )
                        if selection:
                            selected_keyword = f"tell me about {selection}"
                else:
                    st.error("Please login to generate keywords.", icon="🚨")

            # Summary
            with tab4:
                if "user" in st.session_state:
                    if st.button(
                        "Generate Summary",
                        use_container_width=True,
                        icon=":material/summarize:",
                    ):
                        formatted = ai_service.generate_summary(text)
                        if formatted == "error":
                            st.error("Input exceeds model token limit.", icon="🚨")
                        else:
                            st.markdown(
                                f"<div style='height:400px;overflow:auto'>{formatted}</div>",
                                unsafe_allow_html=True,
                            )
                else:
                    st.error("Please login to generate summary.", icon="🚨")

    # --------------------------------------------------
    # Footer
    # --------------------------------------------------
    render_footer()

    # --------------------------------------------------
    # Chat Area
    # --------------------------------------------------
    with st.container():
        st.header(APP_HEADER)
        st.caption(APP_HEADER_CAPTION)

        if uploaded_file is None:
            st.chat_input(helper.get_query_head(""), disabled=True)
            st.stop()

        # ---- Build Vector Store ONCE per file ----
        ai_service.build_vector_store(text)

        chat_input = st.chat_input(query_head)

        if selected_keyword and not chat_input:
            chat_input = selected_keyword
            selected_keyword = None

        if chat_input:
            st.toast("Generating answer... Please wait", icon="🙏")
            response = ai_service.query(chat_input)

            if "user" in st.session_state:
                helper.save_to_db(
                    st.session_state.user["email"],
                    uploaded_file_name,
                    chat_input,
                    re.sub(r"\s+", " ", response).strip(),
                )
            else:
                helper.add_entry(chat_input, response)

        # ---- History ----
        if "user" in st.session_state:
            save_unsaved_after_login()

            collection = helper.client["chat-app"]["chat-data"]
            records = list(
                collection.find(
                    {
                        "email": st.session_state.user["email"],
                        "file_name": uploaded_file_name,
                    }
                )
            )

            for result in reversed(records):
                helper.format_question_answer_signed(result)

        else:
            for result in reversed(st.session_state.response_array):
                formatters.format_question(result["question"])
                formatters.format_answer(result["answer"])


if __name__ == "__main__":
    main()
