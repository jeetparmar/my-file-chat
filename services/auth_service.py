import streamlit as st
import time
from utils.validators import Validators
from config.settings import DEMO_OTP


class AuthService:

    @staticmethod
    def validate_email(email: str) -> bool:
        return Validators.is_valid_email(email)

    @staticmethod
    def validate_emails_list(emails: list) -> bool:
        return Validators.is_valid_emails(emails)

    @staticmethod
    def verify_otp(entered_otp: str) -> bool:
        return entered_otp == DEMO_OTP

    @staticmethod
    def is_user_logged_in() -> bool:
        return "user" in st.session_state

    @staticmethod
    def get_current_user() -> dict:
        if AuthService.is_user_logged_in():
            return st.session_state.user
        return None

    @staticmethod
    def get_current_email() -> str:
        user = AuthService.get_current_user()
        return user["email"] if user else None

    @staticmethod
    def login(email: str) -> bool:
        try:
            st.session_state.user = {"email": email}
            st.toast("Logged in successfully.", icon="🎉")
            time.sleep(1)
            st.rerun()
            return True
        except Exception as e:
            st.error(f"Login failed: {str(e)}", icon="🚨")
            return False

    @staticmethod
    def logout() -> bool:
        try:
            st.toast("Logout successfully.", icon="🎉")
            if "user" in st.session_state:
                del st.session_state["user"]
            time.sleep(1)
            st.rerun()
            return True
        except Exception as e:
            st.error(f"Logout failed: {str(e)}", icon="🚨")
            return False
