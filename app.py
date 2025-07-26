import streamlit as st
import os
import random
import uuid
import pandas as pd
from database import init_db, save_rating, get_rated_images, get_all_ratings
from sqlalchemy import text

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Face Rating Tool")

# --- Database Connection ---
conn = st.connection('ratings_db', type='sql', url='sqlite:///ratings.db')
init_db(conn)

# --- App Routing ---
def rating_page():
    # --- Session Management ---
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    session_id = st.session_state.session_id

    st.title("Face Attractiveness Rating Tool")
    st.write(
        "Rate the face's attractiveness from 1-100. "
        "Click **Skip** for ambiguous images or **Flag** for bad/invalid ones."
    )
    
    # --- Image Loading ---
    IMAGE_DIR = "images/holdout_faces/cropped"
    try:
        all_images = sorted([f for f in os.listdir(IMAGE_DIR) if f.endswith(('.png', '.jpg', '.jpeg'))])
        rated_images = get_rated_images(conn, session_id)
        unrated_images = [img for img in all_images if img not in rated_images]

        # --- Progress Bar ---
        progress = len(rated_images)
        total = len(all_images)
        st.progress(progress / total, text=f"Progress: {progress} / {total} images rated")

        if not unrated_images:
            st.success("🎉 You have rated all available images. Thank you!")
            st.balloons()
            return

        # --- Image Display ---
        if 'current_image' not in st.session_state or st.session_state.current_image not in unrated_images:
            st.session_state.current_image = random.choice(unrated_images)
        current_image = st.session_state.current_image
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(os.path.join(IMAGE_DIR, current_image), width=400)
        
        with col2:
            st.write("### Your Rating")
            rating = st.slider("Rating", 1, 100, 50, label_visibility="collapsed")
            
            # --- Action Buttons ---
            b_col1, b_col2, b_col3 = st.columns(3)
            if b_col1.button("✅ Submit", use_container_width=True):
                save_rating(conn, current_image, rating, session_id)
                st.toast(f"Saved rating of {rating}.", icon="✅")
                st.rerun()

            if b_col2.button("➡️ Skip", use_container_width=True):
                save_rating(conn, current_image, -1, session_id)
                st.toast(f"Skipped image.", icon="➡️")
                st.rerun()

            if b_col3.button("🚩 Flag", use_container_width=True, type="secondary"):
                save_rating(conn, current_image, -2, session_id)
                st.toast(f"Flagged image for review.", icon="🚩")
                st.rerun()
    
    except FileNotFoundError:
        st.error(f"Image directory not found. Please ensure '{IMAGE_DIR}' exists.")
    except (IndexError, KeyError):
        st.success("🎉 You have rated all the available images. Thank you for your contribution!")
        st.balloons()

def dashboard_page():
    st.title("📊 Dashboard")

    # --- Password Protection ---
    password = st.text_input("Enter password to access dashboard", type="password")
    
    # IMPORTANT: Set this password in your Streamlit secrets management
    # It looks for a secret named "DASHBOARD_PASSWORD"
    try:
        correct_password = st.secrets["DASHBOARD_PASSWORD"]
    except FileNotFoundError:
        st.error("Secrets file not found. Please add secrets to your Streamlit app.")
        return
    except KeyError:
        st.error("`DASHBOARD_PASSWORD` not found in secrets. Please set it.")
        return

    if password != correct_password:
        if password: # If user has entered a password but it's wrong
            st.error("Incorrect password.")
        return # Stop execution if password is not correct
    
    st.success("Password correct. Welcome to the dashboard.")
    
    # --- Data Loading and Display ---
    all_ratings_data = get_all_ratings(conn)
    
    if not all_ratings_data:
        st.warning("No ratings have been submitted yet.")
        return

    df = pd.DataFrame(all_ratings_data)
    
    # --- Key Metrics ---
    st.header("Key Metrics")
    total_ratings = len(df)
    valid_ratings = df[df['rating'] > 0].shape[0]
    skipped_count = df[df['rating'] == -1].shape[0]
    flagged_count = df[df['rating'] == -2].shape[0]
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Total Submissions", total_ratings)
    m_col2.metric("Valid Ratings", valid_ratings)
    m_col3.metric("Skipped Images", skipped_count)
    m_col4.metric("Flagged Images", flagged_count)

    # --- Download CSV ---
    st.header("Download Data")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download all ratings as CSV",
        data=csv,
        file_name="face_ratings_export.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    # --- Raw Data View ---
    st.header("Raw Data")
    st.dataframe(df)

# --- Main App Router ---
page = st.query_params.get("page", "rater")

if page == "dashboard":
    dashboard_page()
else:
    rating_page() 