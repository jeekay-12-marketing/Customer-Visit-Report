import firebase_admin
from firebase_admin import credentials, auth, firestore
import streamlit as st

def init_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)

def get_db():
    return firestore.client()
