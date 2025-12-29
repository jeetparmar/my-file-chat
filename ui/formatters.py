import streamlit as st


class UIFormatters:

    @staticmethod
    def format_question(question):
        """Format and display user question"""
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #6e57e0, #9b59b6);
                color: white;
                padding: 12px 15px;
                border-radius: 15px;
                float: right;
                box-shadow: 2px 2px 12px rgba(0,0,0,0.3);
                position: relative;
            ">
                <b>Q: {question}</b>
                <span style="
                    content: '';
                    position: absolute;
                    bottom: -10px;
                    right: 15px;
                    width: 0;
                    height: 0;
                    border-left: 10px solid transparent;
                    border-right: 10px solid transparent;
                    border-top: 10px solid #9b59b6;
                "></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def format_answer(answer):
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #3b3f52, #2c2f3a);
                color: #f1f1f1;
                padding: 12px 15px;
                border-radius: 15px;
                float: left;
                margin-top: 15px;
                box-shadow: 2px 2px 12px rgba(0,0,0,0.3);
                display: flex;
                align-items: start;
                position: relative;
                font-family: 'Arial', sans-serif;
            ">
                <span style='margin-right: 8px; color:#9bffbb; font-weight:bold;'>🤖</span>
                <label style='text-align: justify; line-height: 1.5;'>A: {answer}</label>
                <span style="
                    content: '';
                    position: absolute;
                    bottom: -10px;
                    left: 15px;
                    width: 0;
                    height: 0;
                    border-left: 10px solid transparent;
                    border-right: 10px solid transparent;
                    border-top: 10px solid #2c2f3a;
                "></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
