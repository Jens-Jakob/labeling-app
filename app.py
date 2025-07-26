import streamlit as st
import os
import random
import uuid
from database import init_db, save_rating, get_rated_images

# --- Configuration ---
IMAGE_DIR = "images/holdout_faces/cropped"

# --- Database Connection ---
# Establishes a persistent connection to Streamlit's cloud-native SQLite database.
conn = st.connection('ratings_db', type='sql', url='sqlite:///ratings.db')
init_db(conn)

# --- Session Management ---
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
session_id = st.session_state.session_id

# --- Main Application Logic ---
st.set_page_config(layout="wide")
st.title("Face Attractiveness Rating Tool")
st.write(
    "Rate the face's attractiveness from 1-100. "
    "Click **Skip** for ambiguous images or **Flag** for bad/invalid ones."
)

# --- Load Image Lists & Progress ---
try:
    all_images = sorted([f for f in os.listdir(IMAGE_DIR) if f.endswith(('.png', '.jpg', '.jpeg'))])
    rated_images = get_rated_images(conn, session_id)
    unrated_images = [img for img in all_images if img not in rated_images]

    # --- Progress Bar ---
    progress = len(rated_images)
    total = len(all_images)
    st.progress(progress / total, text=f"Progress: {progress} / {total} images rated")

    if not unrated_images:
        st.success("🎉 You have rated all the available images. Thank you for your contribution!")
        st.balloons()
    else:
        # --- Display an Image ---
        if 'current_image' not in st.session_state or st.session_state.current_image not in unrated_images:
            st.session_state.current_image = random.choice(unrated_images)

        current_image = st.session_state.current_image
        image_path = os.path.join(IMAGE_DIR, current_image)

        col1, col2 = st.columns(2)

        with col1:
            st.image(image_path, caption=f"Image ID: {current_image}", width=400)

        with col2:
            st.write("### Your Rating")
            rating = st.slider("Select a rating (1-100):", 1, 100, 50, label_visibility="collapsed")

            # --- Action Buttons ---
            submit_button = st.button("✅ Submit Rating", use_container_width=True)
            skip_button = st.button("➡️ Skip Image", use_container_width=True)
            flag_button = st.button("🚩 Flag as Invalid", use_container_width=True, type="secondary")

            def advance_image():
                """Selects the next random image and reruns the app."""
                remaining_images = [img for img in unrated_images if img != current_image]
                if remaining_images:
                    st.session_state.current_image = random.choice(remaining_images)
                else:
                    del st.session_state.current_image
                st.rerun()

            if submit_button:
                save_rating(conn, current_image, rating, session_id)
                st.toast(f"Saved rating of {rating} for {current_image}.", icon="✅")
                advance_image()

            if skip_button:
                save_rating(conn, current_image, -1, session_id) # -1 for skip
                st.toast(f"Skipped image {current_image}.", icon="➡️")
                advance_image()

            if flag_button:
                save_rating(conn, current_image, -2, session_id) # -2 for flag
                st.toast(f"Flagged image {current_image} for review.", icon="🚩")
                advance_image()


except FileNotFoundError:
    st.error(f"Image directory not found. Please make sure '{IMAGE_DIR}' exists.")
except (IndexError, KeyError):
    # This can happen if the last image is processed and state is cleared
    st.success("🎉 You have rated all the available images. Thank you for your contribution!")
    st.balloons()
except Exception as e:
    st.error(f"An unexpected error occurred: {e}") 