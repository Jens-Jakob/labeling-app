import streamlit as st
import os
import random
import pandas as pd
from database import init_db, save_rating, get_rated_images, get_all_ratings
from sqlalchemy import text
from st_keyup import st_keyup

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Face Rating Tool")

# --- Database Connection ---
conn = st.connection('ratings_db', type='sql', url='sqlite:///ratings.db')
init_db(conn)

# --- App Logic ---

def show_rating_interface(user_identifier):
    """The main UI for rating images."""
    st.title("Face Attractiveness Rating Tool")
    st.write(
        "Use the slider to rate, or use keyboard shortcuts: **Enter** (Submit), **Space** (Skip), **F** (Flag)."
    )
    
    # --- Image Loading ---
    IMAGE_DIR = "images/holdout_faces/cropped"
    try:
        all_images = sorted([f for f in os.listdir(IMAGE_DIR) if f.endswith(('.png', '.jpg', '.jpeg'))])
        rated_images = get_rated_images(conn, user_identifier)
        unrated_images = [img for img in all_images if img not in rated_images]

        st.progress(len(rated_images) / len(all_images), text=f"Progress: {len(rated_images)} / {len(all_images)}")

        if not unrated_images:
            st.success("🎉 You have rated all available images. Thank you!")
            st.balloons()
            return

        if 'current_image' not in st.session_state or st.session_state.current_image not in unrated_images:
            st.session_state.current_image = random.choice(unrated_images)
        current_image = st.session_state.current_image
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(os.path.join(IMAGE_DIR, current_image), width=400)
        
        with col2:
            st.write("### Your Rating")
            rating = st.slider("Rating", 1, 100, 50, label_visibility="collapsed")
            
            # --- Keyboard Shortcuts ---
            key = st_keyup("Enter for submit, Space for skip, F for flag", debounce=500, key="keyup")

            if key == "Enter":
                save_rating(conn, current_image, rating, user_identifier)
                st.toast(f"Saved rating of {rating}.", icon="✅")
                st.rerun()
            elif key == " ": # Space bar
                save_rating(conn, current_image, -1, user_identifier)
                st.toast("Skipped image.", icon="➡️")
                st.rerun()
            elif key and key.lower() == 'f':
                save_rating(conn, current_image, -2, user_identifier)
                st.toast("Flagged image for review.", icon="🚩")
                st.rerun()
                
    except FileNotFoundError:
        st.error(f"Image directory not found. Please ensure '{IMAGE_DIR}' exists.")
    except (IndexError, KeyError):
        st.success("🎉 You have rated all the available images. Thank you for your contribution!")
        st.balloons()

def dashboard_page():
    st.title("📊 Dashboard")
    password = st.text_input("Enter password", type="password")
    
    try:
        correct_password = st.secrets["DASHBOARD_PASSWORD"]
    except Exception:
        st.error("Dashboard password not set in Streamlit Secrets.")
        return

    if password != correct_password:
        if password: st.error("Incorrect password.")
        return
    
    st.success("Welcome to the dashboard.")
    
    all_ratings = get_all_ratings(conn)
    if not all_ratings:
        st.warning("No ratings submitted yet.")
        return

    df = pd.DataFrame(all_ratings)
    
    st.header("Key Metrics")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Total Submissions", len(df))
    m_col2.metric("Valid Ratings", df[df['rating'] > 0].shape[0])
    m_col3.metric("Skipped", df[df['rating'] == -1].shape[0])
    m_col4.metric("Flagged", df[df['rating'] == -2].shape[0])

    st.header("Download Data")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download all ratings as CSV", csv, "face_ratings_export.csv", "text/csv", use_container_width=True)
    
    st.header("Raw Data")
    st.dataframe(df)

def main_app():
    """Main application router."""
    page = st.query_params.get("page", "rater")

    if page == "dashboard":
        dashboard_page()
    else:
        if 'user_identifier' not in st.session_state:
            st.title("Welcome to the Face Rating Tool!")
            st.write("Please enter a name or unique ID to begin.")
            user_id = st.text_input("Your Name/ID")
            if st.button("Start Rating"):
                if user_id:
                    st.session_state.user_identifier = user_id
                    st.rerun()
                else:
                    st.error("Please enter a name or ID.")
        else:
            show_rating_interface(st.session_state.user_identifier)

if __name__ == "__main__":
    main_app() 