import streamlit as st
import os
import random
import uuid
import pandas as pd
from database import init_db, save_rating, get_rated_images, get_all_ratings, get_flagged_images, get_image_statistics, get_user_statistics
from sqlalchemy import text

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
        "Rate the face's attractiveness from 1.0-10.0 (e.g., 7.5). "
        "Click **Skip** for ambiguous images or **Flag** for bad/invalid ones."
    )
    
    # --- Image Loading ---
    IMAGE_DIR = "images/holdout_faces/cropped"
    try:
        all_images = sorted([f for f in os.listdir(IMAGE_DIR) if f.endswith(('.png', '.jpg', '.jpeg'))])
        rated_images = get_rated_images(conn, user_identifier)
        unrated_images = [img for img in all_images if img not in rated_images]

        # --- Progress Bar ---
        st.progress(len(rated_images) / len(all_images), text=f"Progress: {len(rated_images)} / {len(all_images)} images rated")

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
            rating = st.slider("Rating", 1.0, 10.0, 5.0, step=0.1, label_visibility="collapsed")
            
            b_col1, b_col2, b_col3 = st.columns(3)
            if b_col1.button("✅ Submit", use_container_width=True):
                save_rating(conn, current_image, rating, user_identifier)
                st.toast(f"Saved rating of {rating:g}.", icon="✅")
                st.rerun()

            if b_col2.button("➡️ Skip", use_container_width=True):
                save_rating(conn, current_image, -1, user_identifier)
                st.toast(f"Skipped image.", icon="➡️")
                st.rerun()

            if b_col3.button("🚩 Flag", use_container_width=True, type="secondary"):
                save_rating(conn, current_image, -2, user_identifier)
                st.toast(f"Flagged image for review.", icon="🚩")
                st.rerun()
    
    except FileNotFoundError:
        st.error(f"Image directory not found. Please ensure '{IMAGE_DIR}' exists.")
    except (IndexError, KeyError):
        st.success("🎉 You have rated all the available images. Thank you for your contribution!")
        st.balloons()

def dashboard_page():
    st.title("📊 Analytics Dashboard")
    
    # Password protection
    password = st.text_input("Enter password", type="password")
    try:
        correct_password = st.secrets["DASHBOARD_PASSWORD"]
    except Exception:
        st.error("Dashboard password not set in Streamlit Secrets.")
        return

    if password != correct_password:
        if password: st.error("Incorrect password.")
        return
    
    st.success("Welcome to the analytics dashboard.")
    
    # Check if there's data
    all_ratings = get_all_ratings(conn)
    if not all_ratings:
        st.warning("No ratings submitted yet.")
        return

    # Create tabs for different analytics
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Overview", "🖼️ Image Analytics", "🚩 Flagged Images", "👥 User Analytics", "📥 Export Data"])
    
    with tab1:
        st.header("Overview")
        df = pd.DataFrame(all_ratings)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Submissions", len(df))
        col2.metric("Valid Ratings", len(df[df['rating'] > 0]))
        col3.metric("Skipped", len(df[df['rating'] == -1]))
        col4.metric("Flagged", len(df[df['rating'] == -2]))
        
        # Rating distribution
        valid_ratings = df[df['rating'] > 0]['rating']
        if len(valid_ratings) > 0:
            st.subheader("Rating Distribution")
            fig_data = valid_ratings.value_counts().sort_index()
            st.bar_chart(fig_data)
            
            col1, col2 = st.columns(2)
            col1.metric("Average Rating", f"{valid_ratings.mean():.1f}")
            col2.metric("Rating Std Dev", f"{valid_ratings.std():.1f}")
    
    with tab2:
        st.header("Image Analytics")
        image_stats = get_image_statistics(conn)
        
        if image_stats:
            df_images = pd.DataFrame(image_stats)
            df_images = df_images.fillna(0)  # Handle NaN values
            
            # Add controversy score (high when ratings vary a lot)
            df_images['controversy_score'] = df_images['max_rating'] - df_images['min_rating']
            df_images['controversy_score'] = df_images['controversy_score'].fillna(0)
            
            st.subheader("Top Rated Images")
            top_rated = df_images[df_images['valid_ratings'] >= 2].nlargest(10, 'avg_rating')
            if not top_rated.empty:
                st.dataframe(top_rated[['image_id', 'avg_rating', 'valid_ratings', 'controversy_score']], use_container_width=True)
            
            st.subheader("Most Controversial Images")
            controversial = df_images[df_images['valid_ratings'] >= 3].nlargest(10, 'controversy_score')
            if not controversial.empty:
                st.dataframe(controversial[['image_id', 'avg_rating', 'controversy_score', 'valid_ratings']], use_container_width=True)
            
            st.subheader("All Image Statistics")
            st.dataframe(df_images, use_container_width=True)
        else:
            st.info("No image statistics available yet.")
    
    with tab3:
        st.header("Flagged Images Review")
        flagged_images = get_flagged_images(conn)
        
        if flagged_images:
            st.warning(f"Found {len(flagged_images)} flagged images that need review:")
            
            for img_id in flagged_images:
                with st.expander(f"🚩 {img_id}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Try to find the image with correct path and extension
                        image_found = False
                        for ext in ['.png', '.jpg', '.jpeg']:
                            img_path = f"images/holdout_faces/cropped/{img_id}"
                            if not img_path.endswith(ext):
                                img_path_with_ext = img_path + ext if '.' not in img_id else img_path
                            else:
                                img_path_with_ext = img_path
                            
                            try:
                                if os.path.exists(img_path_with_ext):
                                    st.image(img_path_with_ext, width=300)
                                    image_found = True
                                    break
                            except Exception:
                                continue
                        
                        if not image_found:
                            st.info(f"Image preview not available for {img_id}")
                    
                    with col2:
                        # Show flag count for this image
                        flags_df = pd.DataFrame(all_ratings)
                        flag_count = len(flags_df[(flags_df['image_id'] == img_id) & (flags_df['rating'] == -2)])
                        st.metric("Times Flagged", flag_count)
                        
                        st.info("Review this image and consider removing it from your dataset if it's inappropriate or poor quality.")
        else:
            st.success("No flagged images. All images appear to be appropriate.")
    
    with tab4:
        st.header("User Analytics & Data Quality")
        user_stats = get_user_statistics(conn)
        
        if user_stats:
            df_users = pd.DataFrame(user_stats)
            df_users = df_users.fillna(0)
            
            st.subheader("Top Contributors")
            st.dataframe(df_users.head(10), use_container_width=True)
            
            st.subheader("Potential Data Quality Issues")
            
            # Flag users with suspicious patterns
            suspicious_users = df_users[
                (df_users['avg_rating'] == df_users['avg_rating'].max()) |  # Always max rating
                (df_users['avg_rating'] == df_users['avg_rating'].min()) |  # Always min rating
                (df_users['flags'] / df_users['total_submissions'] > 0.5)   # Flag more than half
            ]
            
            if not suspicious_users.empty:
                st.warning("Users with potentially suspicious rating patterns:")
                st.dataframe(suspicious_users, use_container_width=True)
            else:
                st.success("No obvious data quality issues detected.")
                
            st.subheader("All User Statistics")
            st.dataframe(df_users, use_container_width=True)
        else:
            st.info("No user statistics available yet.")
    
    with tab5:
        st.header("Export Data")
        df = pd.DataFrame(all_ratings)
        
        st.subheader("Download Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Full dataset
            csv_all = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download All Ratings",
                csv_all,
                "all_ratings.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col2:
            # Valid ratings only
            valid_only = df[df['rating'] > 0]
            if not valid_only.empty:
                csv_valid = valid_only.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Valid Ratings Only",
                    csv_valid,
                    "valid_ratings.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        st.subheader("Data Preview")
        st.dataframe(df.head(20), use_container_width=True)

def main_app():
    """Main application router."""
    # Debug: Show what page parameter we're getting
    try:
        page = st.query_params.get("page", "rater")
        st.sidebar.write(f"Debug: page = '{page}'")  # Temporary debug info
    except Exception as e:
        st.sidebar.write(f"Debug: Error getting page param: {e}")
        page = "rater"
    
    # Add navigation in sidebar
    st.sidebar.title("Navigation")
    if st.sidebar.button("📊 Go to Dashboard"):
        st.query_params.page = "dashboard"
        st.rerun()
    if st.sidebar.button("⭐ Go to Rating Tool"):
        st.query_params.page = "rater"
        st.rerun()

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