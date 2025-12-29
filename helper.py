import os
import uuid
import time
import tempfile
import pandas as pd
import streamlit as st
import re
from datetime import datetime
from PyPDF2 import PdfReader
from pydub import AudioSegment
from pymongo import MongoClient
import speech_recognition as sr
from moviepy import VideoFileClip
from bson.objectid import ObjectId
from openai import OpenAI
from transformers import pipeline, T5Tokenizer, T5ForConditionalGeneration
from sklearn.feature_extraction.text import TfidfVectorizer

from config.settings import (
    DB_NAME,
    DEMO_OTP,
    ICON_URL,
    MONGODB_CONNECTION_STRING,
)
from ui.formatters import UIFormatters

formatters = UIFormatters()


class Helper:
    query_head = "Ask questions from your file"

    client = MongoClient(MONGODB_CONNECTION_STRING)

    def __init__(self):
        pass

    def get_footer(self):
        return self.footer

    def get_query_head(self, param):
        return "Ask questions from your {} file".format(param)

    def add_entry(self, question, answer):
        st.session_state.response_array.append({"question": question, "answer": answer})

    def save_to_db(self, email, file_name, question, answer):
        self.client[DB_NAME]["chat-data"].insert_one(
            {
                "email": email,
                "file_name": file_name,
                "question": question,
                "answer": answer,
                "created_at": datetime.now(),
            }
        )

    def after_signed_in(self, email):
        with st.popover(email, icon=":material/mail:", use_container_width=True):
            st.button(
                "New Group",
                use_container_width=False,
                icon=":material/group_add:",
                type="tertiary",
                on_click=self.create_group,
            )
            st.html("<hr />")
            st.button(
                "My Groups",
                use_container_width=False,
                icon=":material/groups:",
                type="tertiary",
                on_click=self.groups,
            )
            st.button(
                "My Favorite",
                use_container_width=False,
                icon="❤️",
                type="tertiary",
                on_click=self.my_favorite,
            )
            st.button(
                "My History",
                use_container_width=False,
                icon=":material/history:",
                type="tertiary",
                on_click=self.history,
            )
            st.html("<hr />")
            st.button(
                "Shared by me",
                use_container_width=False,
                icon=":material/share:",
                type="tertiary",
                on_click=self.shared_by_me,
            )
            st.button(
                "Shared with me",
                use_container_width=False,
                icon=":material/share:",
                type="tertiary",
                on_click=self.shared_with_me,
            )
            st.html("<hr />")
            st.button(
                "Settings",
                use_container_width=False,
                icon=":material/settings:",
                type="tertiary",
                disabled=True,
            )
            if st.button(
                "Logout",
                use_container_width=False,
                icon=":material/logout:",
                type="tertiary",
            ):
                st.toast("Logout successfully.", icon="🎉")
                del st.session_state["user"]
                time.sleep(1)
                st.rerun()

    @st.dialog("Please Login")
    def sign_in(self):
        email = st.text_input(
            "Email Address", placeholder="Enter Email Address", autocomplete="off"
        )
        otp = st.text_input(
            "OTP",
            max_chars=6,
            type="password",
            placeholder="Enter one time password",
            autocomplete="off",
        )
        if st.button("Submit"):
            if email == "":
                st.error("Please enter email", icon="🚨")
            elif otp == "":
                st.error("Please enter otp", icon="🚨")
            elif otp != DEMO_OTP:
                st.error("Please enter valid otp", icon="🚨")
            else:
                st.session_state.user = {"email": email}
                st.toast("Logged in successfully.", icon="🎉")
                st.rerun()

    def delete_from_history(self, id):
        collection = self.client[DB_NAME]["chat-data"]
        collection.delete_one({"_id": ObjectId(id)})

    def delete_group(self, id):
        collection = self.client[DB_NAME]["group-data"]
        collection.delete_one({"_id": ObjectId(id)})

    @st.dialog("Please Share in Group")
    def share_in_group(self, id):
        groups = []
        group_collection = self.client[DB_NAME]["group-data"]
        records = list(
            group_collection.find({"group_admin": st.session_state.user["email"]})
        )
        for record in records:
            groups.append(record["group_name"])

        selected_group = st.selectbox(
            "Select Group",
            groups,
            index=None,
            placeholder="Choose Group",
        )

        group_object = None
        for record in records:
            if selected_group == record["group_name"]:
                group_object = record

        if st.button("Share"):
            if selected_group is None:
                st.error("Please select group", icon="🚨")
            else:
                chat_collection = self.client[DB_NAME]["chat-data"]
                chat_collection.update_one(
                    {"_id": id}, {"$addToSet": {"shared_in_group": selected_group}}
                )
                if "shared_qa_count" in group_object:
                    shared_qa_count = group_object["shared_qa_count"]
                else:
                    shared_qa_count = 0
                group_collection.update_one(
                    {
                        "group_admin": st.session_state.user["email"],
                        "group_name": selected_group,
                    },
                    {"$set": {"shared_qa_count": shared_qa_count + 1}},
                )
                st.toast("Shared in group successfully.", icon="🎉")
                st.rerun()

    @st.dialog("Please Share")
    def share(self, id):
        email = st.text_input(
            "Email Address", placeholder="Enter Email Address", autocomplete="off"
        )
        if st.button("Share"):
            if email == "":
                st.error("Please enter email", icon="🚨")
            else:
                collection = self.client[DB_NAME]["chat-data"]
                collection.update_one(
                    {"_id": id}, {"$addToSet": {"shared_with": email}}
                )
                st.rerun()

    def favorite(self, id, is_favorite):
        collection = self.client[DB_NAME]["chat-data"]
        collection.update_one({"_id": id}, {"$set": {"favorite": is_favorite}})

    @st.dialog("Shared by me", width="large")
    def shared_by_me(self):
        collection = self.client[DB_NAME]["chat-data"]
        records = list(
            collection.find(
                {
                    "email": st.session_state.user["email"],
                    "shared_with": {"$exists": True, "$ne": []},
                }
            )
        )
        if len(records) > 0:
            for result in reversed(records):
                self.format_question_answer_signed(result)
        else:
            st.write("No shared history")

    @st.dialog("Shared with me", width="large")
    def shared_with_me(self):
        email = st.session_state.user["email"]
        chat_collection = self.client[DB_NAME]["chat-data"]
        chat_records = list(chat_collection.find({"shared_with": email}))

        chat_group_records_count = 0
        chat_records_count = len(chat_records)

        group_collection = self.client[DB_NAME]["group-data"]
        group_records = list(group_collection.find({"members": {"$in": [email]}}))
        if len(group_records) > 0:
            group_names = []
            for group_result in reversed(group_records):
                group_names.append(group_result["group_name"])
            if len(group_names) > 0:
                chat_group_records = list(
                    chat_collection.find({"shared_in_group": {"$in": group_names}})
                )
                chat_group_records_count = len(chat_group_records)
                if chat_group_records_count > 0:
                    for chat_result in reversed(chat_group_records):
                        self.format_question_answer_signed(chat_result)

        if chat_records_count == 0 and chat_group_records_count == 0:
            st.write("No shared history")

        if chat_records_count > 0:
            for chat_result in reversed(chat_records):
                self.format_question_answer_signed(chat_result)

    @st.dialog("My Favorite", width="large")
    def my_favorite(self):
        collection = self.client[DB_NAME]["chat-data"]
        records = list(
            collection.find({"email": st.session_state.user["email"], "favorite": True})
        )
        if len(records) > 0:
            for result in reversed(records):
                self.format_question_answer_signed(result)
        else:
            st.write("No favorite data")

    @st.dialog("My History", width="large")
    def history(self):
        collection = self.client[DB_NAME]["chat-data"]
        records = list(collection.find({"email": st.session_state.user["email"]}))
        if len(records) > 0:
            for result in reversed(records):
                self.format_question_answer_signed(result)
        else:
            st.write("No saved history")

    def is_valid_email(self, email):
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_regex, email) is not None

    @st.dialog("New Group")
    def create_group(self):
        group_name = st.text_input(
            "Group Name", placeholder="Enter Group Name", autocomplete="off"
        )
        emails = st.text_area(
            "Email Addresses", placeholder="Enter Email Addresses (seperated by comma)"
        )
        if st.button("Create Group"):
            if group_name == "":
                st.error("Please add group name", icon="🚨")
            elif emails == "":
                st.error("Please add emails", icon="🚨")
            else:
                email_list = emails.replace(" ", "").split(",")
                if len(email_list) > 1:
                    for email in email_list:
                        if self.is_valid_email(email) == False:
                            st.error("Please enter valid emails", icon="🚨")
                            return
                    collection = self.client[DB_NAME]["group-data"]
                    collection.insert_one(
                        {
                            "group_admin": st.session_state.user["email"],
                            "group_name": group_name,
                            "members": email_list,
                            "created_at": datetime.now(),
                        }
                    )
                    st.toast("Group created successfully.", icon="🎉")
                    st.rerun()
                else:
                    st.error("Please add atleast 2 emails", icon="🚨")

    @st.dialog("My Groups", width="large")
    def groups(self):
        collection = self.client[DB_NAME]["group-data"]
        records = list(collection.find({"group_admin": st.session_state.user["email"]}))
        if len(records) > 0:
            group_names = []
            members = []
            shared_qa_count = []
            created_at = []

            for record in records:
                group_names.append(record["group_name"])
                members.append(record["members"])
                created_at.append(self.time_ago(record["created_at"]))
                if "shared_qa_count" in record:
                    shared_qa_count.append(record["shared_qa_count"])
                else:
                    shared_qa_count.append(0)

            df = pd.DataFrame(
                {
                    "name": group_names,
                    "members": members,
                    "shared_qa_count": shared_qa_count,
                    "created_at": created_at,
                }
            )
            st.data_editor(
                df,
                column_config={
                    "name": "Name",
                    "members": "Members",
                    "shared_qa_count": "Shared QA count",
                    "created_at": "Created At",
                },
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.write("No group(s), please create one")

    def format_text(self, input_text):
        # Format headers
        formatted_text = re.sub(r"### (.+)", r"### \1", input_text)
        # Format bold text
        formatted_text = re.sub(r"\*\*(.+?)\*\*", r"**\1**", formatted_text)
        return formatted_text

    def type_text(self, text, delay=0.05):
        placeholder = st.empty()
        typed_text = ""
        for char in text:
            typed_text += char
            placeholder.html(
                f"""
                <div style='display: flex; align-items: start;'>
                    <img src='{ICON_URL}' style='width: 20px; margin-right: 10px;margin-top:0px;'>
                    <label style='text-align: justify'>{typed_text}</label>
                </div>
                """
            )
            time.sleep(delay)

    def generate_keywords(self, generated_text, count):
        documents = [generated_text]
        vectorizer = TfidfVectorizer(stop_words="english")
        X = vectorizer.fit_transform(documents)
        terms = vectorizer.get_feature_names_out()
        tfidf_scores = X.toarray()[0]
        term_scores = {terms[i]: tfidf_scores[i] for i in range(len(terms))}
        sorted_terms = sorted(term_scores.items(), key=lambda x: x[1], reverse=True)
        return [term for term, score in sorted_terms[:count]]

    def generate_questions(self, generated_text, count):
        model_name = "valhalla/t5-small-qg-prepend"
        tokenizer = T5Tokenizer.from_pretrained(model_name)
        model = T5ForConditionalGeneration.from_pretrained(model_name)
        input_ids = tokenizer.encode(generated_text, return_tensors="pt")
        outputs = model.generate(
            input_ids=input_ids,
            max_length=64,
            num_beams=count,
            num_return_sequences=count,
            early_stopping=True,
        )
        return [
            tokenizer.decode(output, skip_special_tokens=True) for output in outputs
        ]

    def reset_entries(self):
        st.session_state["text"] = ""
        st.session_state["input_query"] = ""
        st.session_state["response_array"] = []

    def format_question_answer_signed(self, result):
        col1, col2 = st.columns([8, 1])
        with col1:
            formatters.format_question(result["question"])
        with col2:
            with st.popover("", icon=":material/more_vert:"):
                if "shared_with" in result:
                    st.button(
                        f"Share ({len(result['shared_with'])})",
                        help=f"Shared with: {', '.join(result['shared_with'])}",
                        key=uuid.uuid4(),
                        icon=":material/share:",
                        type="tertiary",
                        args=[result["_id"]],
                        on_click=self.share,
                    )
                else:
                    st.button(
                        "Share (0)",
                        help="Please share",
                        key=uuid.uuid4(),
                        icon=":material/share:",
                        type="tertiary",
                        args=[result["_id"]],
                        on_click=self.share,
                    )
                if "shared_in_group" in result:
                    st.button(
                        f"Group Share ({len(result['shared_in_group'])})",
                        help=f"Shared Group: {', '.join(result['shared_in_group'])}",
                        key=uuid.uuid4(),
                        icon=":material/share:",
                        type="tertiary",
                        args=[result["_id"]],
                        on_click=self.share_in_group,
                    )
                else:
                    st.button(
                        "Group Share (0)",
                        help="Please share in group",
                        key=uuid.uuid4(),
                        icon=":material/share:",
                        type="tertiary",
                        args=[result["_id"]],
                        on_click=self.share_in_group,
                    )
                if "favorite" in result and result["favorite"] == True:
                    st.button(
                        "Favorite",
                        help="Remove from favorite",
                        key=uuid.uuid4(),
                        icon="❤️",
                        type="tertiary",
                        args=[result["_id"], False],
                        on_click=self.favorite,
                    )
                else:
                    st.button(
                        "Favorite",
                        help="Mark as favorite",
                        key=uuid.uuid4(),
                        icon=":material/favorite:",
                        type="tertiary",
                        args=[result["_id"], True],
                        on_click=self.favorite,
                    )
                if result["email"] == st.session_state.user["email"]:
                    st.button(
                        "Delete",
                        help="Delete",
                        key=uuid.uuid4(),
                        icon=":material/delete:",
                        type="tertiary",
                        args=[result["_id"]],
                        on_click=self.delete_from_history,
                    )
        formatters.format_answer(result["answer"])
        st.markdown(
            f"""
            <div style="font-size: 12px; float:left; margin-left: 5px; margin-top: 5px;">
                <label>Source: <b>{result["file_name"]}</b></label>
            </div>
            <div style="font-size: 12px; float:right; margin-right: 5px;; margin-top: 5px;">
                <label>Asked: <b>{self.time_ago(result["created_at"])}</b></label>
            </div>""",
            unsafe_allow_html=True,
        )

    def time_ago(self, input_time):
        now = datetime.now()
        diff = now - input_time
        seconds = diff.total_seconds()
        minutes = seconds // 60
        hours = minutes // 60
        days = hours // 24
        if seconds < 60:
            return f"{int(seconds)} seconds ago"
        elif minutes < 60:
            return f"{int(minutes)} minutes ago"
        elif hours < 24:
            return f"{int(hours)} hours ago"
        else:
            return f"{int(days)} days ago"

    def split_audio(self, audio_path, chunk_duration=30):
        audio = AudioSegment.from_wav(audio_path)
        chunks = []
        for i in range(0, len(audio), chunk_duration * 1000):
            chunks.append(audio[i : i + chunk_duration * 1000])
        return chunks

    def transcribe_audio_chunks(self, audio_chunks):
        recognizer = sr.Recognizer()
        transcribed_text = []
        for i, chunk in enumerate(audio_chunks):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_chunk:
                chunk.export(temp_chunk.name, format="wav")
                with sr.AudioFile(temp_chunk.name) as source:
                    try:
                        audio_data = recognizer.record(source)
                        text = recognizer.recognize_google(audio_data)
                        transcribed_text.append(text)
                    except sr.UnknownValueError:
                        transcribed_text.append("[Unintelligible]")
                    except sr.RequestError as e:
                        transcribed_text.append(f"[Error: {e}]")
                os.remove(temp_chunk.name)
        return " ".join(transcribed_text)

    def extract_text_from_uploaded_video(self, uploaded_file):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                temp_video.write(uploaded_file.read())
                temp_video_path = temp_video.name
            video = VideoFileClip(temp_video_path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                video.audio.write_audiofile(temp_audio.name, codec="pcm_s16le")
                temp_audio_path = temp_audio.name
            audio_chunks = self.split_audio(temp_audio_path)
            os.remove(temp_video_path)
            os.remove(temp_audio_path)
            return self.transcribe_audio_chunks(audio_chunks)
        except Exception as e:
            st.error("Extraction failed.", icon="🚨")
            return f"Error: {e}"

    def extract_text_from_uploaded_audio(self, uploaded_file):
        try:
            with sr.AudioFile(uploaded_file) as source:
                recognizer = sr.Recognizer()
                audio = recognizer.record(source)
                return recognizer.recognize_google(audio)
        except Exception as e:
            st.error("Extraction failed.", icon="🚨")
            return f"Error: {e}"

    def extract_text_and_display_pdf(self, uploaded_file):
        generatedText = ""
        for page in PdfReader(uploaded_file).pages:
            generatedText += page.extract_text()
        return generatedText
