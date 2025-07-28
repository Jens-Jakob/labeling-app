# Face Attractiveness Rating Web Application

A web-based tool for collecting human ratings of facial attractiveness, built with Streamlit and designed for machine learning research.

## 🎯 Overview

This application enables researchers to collect large-scale human ratings of facial attractiveness through a clean, web-based interface. Users can rate images on a 1.0-10.0 scale (with 0.1 increments), skip ambiguous images, or flag inappropriate content. The system includes comprehensive analytics and data quality monitoring.

## ✨ Features

### 🔧 Core Functionality
- **Image Rating Interface**: Clean, intuitive slider-based rating system (1.0-10.0 scale with decimal precision)
- **User Identification**: Traceable ratings with user-provided identifiers
- **Quality Control**: Skip and flag options for maintaining dataset quality
- **Progress Tracking**: Real-time progress bars for user engagement
- **Persistent Storage**: Cloud-based SQLite database with automatic persistence

### 📊 Analytics Dashboard
- **Overview Analytics**: Total submissions, rating distribution, and key metrics
- **Image Statistics**: Per-image analytics including average ratings and controversy scores
- **Flagged Images Review**: Visual review of problematic images with management tools
- **User Analytics**: Contributor tracking and data quality monitoring
- **Data Export**: Multiple export formats (CSV) with filtering options

### 🛡️ Data Quality Features
- **Duplicate Prevention**: Users cannot rate the same image twice
- **Quality Detection**: Automatic identification of suspicious rating patterns
- **Content Moderation**: User-driven flagging system for inappropriate content
- **Session Management**: Secure, anonymous user tracking without requiring login

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Streamlit (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Deployment**: Streamlit Community Cloud
- **Version Control**: Git/GitHub

### Database Schema
```sql
CREATE TABLE ratings (
    id TEXT PRIMARY KEY,
    image_id TEXT NOT NULL,
    rating REAL NOT NULL,
    user_identifier TEXT NOT NULL,
    timestamp DATETIME NOT NULL
);
```

### Project Structure
```
web_rater/
├── app.py              # Main Streamlit application
├── database.py         # Database operations and queries
├── requirements.txt    # Python dependencies
└── images/
    └── holdout_faces/
        └── cropped/    # Image files for rating
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Streamlit account (for deployment)
- GitHub account (for hosting code)

### Local Development
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   streamlit run app.py
   ```

### Deployment
The application is designed for deployment on Streamlit Community Cloud:
1. Push code to GitHub repository
2. Connect Streamlit Cloud to your repository
3. Set up secrets (dashboard password)
4. Deploy automatically

## 🔐 Configuration

### Required Secrets
Set up in Streamlit Cloud dashboard under "Secrets":
```toml
DASHBOARD_PASSWORD = "your_secure_password_here"
```

### Navigation
- **Main App**: `https://your-app.streamlit.app/`
- **Dashboard**: `https://your-app.streamlit.app/?page=dashboard`
- **Sidebar Navigation**: Use built-in navigation buttons

## 📈 Usage Workflow

### For Researchers
1. **Setup**: Deploy app and configure dashboard password
2. **Data Collection**: Share public URL with raters
3. **Monitoring**: Use dashboard to track progress and quality
4. **Export**: Download data in CSV format for analysis
5. **Quality Control**: Review flagged images and remove problematic content

### For Raters
1. **Access**: Visit the public application URL
2. **Identify**: Enter name or unique identifier
3. **Rate**: Use slider to rate facial attractiveness (1.0-10.0 with 0.1 increments)
4. **Actions**: Submit rating, skip unclear images, or flag inappropriate content
5. **Progress**: Track completion through progress bar

## 📊 Analytics Features

### Dashboard Tabs

#### 1. Overview Tab
- Total submissions and breakdowns (valid, skipped, flagged)
- Rating distribution histogram
- Average rating and standard deviation

#### 2. Image Analytics Tab
- Top-rated images (highest average scores)
- Most controversial images (highest rating variance)
- Complete per-image statistics

#### 3. Flagged Images Review Tab
- Visual review of flagged content
- Flag frequency counts
- Image management recommendations

#### 4. User Analytics Tab
- Top contributor leaderboard
- Data quality issue detection
- Suspicious pattern identification

#### 5. Export Data Tab
- Full dataset download
- Valid ratings only export
- Data preview functionality

## 🔍 Data Quality Monitoring

### Automatic Detection
- **Always Maximum/Minimum**: Users who consistently rate at extremes
- **Excessive Flagging**: Users who flag >50% of images
- **Rating Patterns**: Detection of non-human rating behaviors

### Quality Control Tools
- **Image Flagging**: Community-driven content moderation
- **Skip Functionality**: Allows users to bypass ambiguous content
- **User Tracking**: Identify and potentially exclude problematic raters

## 📝 API Reference

### Database Functions
- `init_db(conn)`: Initialize database schema
- `save_rating(conn, image_id, rating, user_identifier)`: Store new rating
- `get_rated_images(conn, user_identifier)`: Get user's completed ratings
- `get_all_ratings(conn)`: Retrieve all ratings data
- `get_flagged_images(conn)`: Get list of flagged images
- `get_image_statistics(conn)`: Calculate per-image analytics
- `get_user_statistics(conn)`: Generate user analytics

### Special Rating Values
- **1.0-10.0**: Valid attractiveness ratings (with decimal precision)
- **-1**: Skipped image (ambiguous/unclear)
- **-2**: Flagged image (inappropriate/poor quality)

## 🔧 Troubleshooting

### Common Issues
1. **Dashboard Access**: Use sidebar navigation buttons if URL parameters fail
2. **Image Loading**: Check file paths and extensions in flagged images review
3. **Password Issues**: Verify dashboard password is set in Streamlit secrets
4. **Database Errors**: Ensure proper SQLAlchemy connection setup

### Debug Features
- Sidebar debug information shows current page parameter
- Error handling for missing images and database issues
- Graceful fallbacks for various failure modes

## 📊 Data Export Format

### CSV Structure
```csv
id,image_id,rating,user_identifier,timestamp
uuid1,face_00001.png,7.5,UserName,2025-01-01 12:00:00
uuid2,face_00002.png,-1,UserName,2025-01-01 12:01:00
uuid3,face_00003.png,-2,UserName,2025-01-01 12:02:00
```

## 🚀 Scaling Considerations

### Current Limitations
- Images stored in GitHub repository (limited to ~100 images)
- SQLite database (suitable for moderate scale)
- Single-instance deployment

### Future Enhancements
- Cloud storage integration (Cloudflare R2) for large image datasets
- Distributed database for high-volume data collection
- Advanced analytics and machine learning integration

## 🤝 Contributing

### Development Workflow
1. Make changes locally
2. Test with `streamlit run app.py`
3. Commit changes to Git
4. Push to GitHub (auto-deploys)

### Key Files
- `app.py`: Main application logic and UI
- `database.py`: All database operations
- `requirements.txt`: Python dependencies

## 📄 License

This project is developed for research purposes. Please ensure compliance with your institution's data collection and privacy policies when collecting human ratings.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review Streamlit Cloud logs for deployment issues
3. Verify database connection and secrets configuration

---

**Built with ❤️ for machine learning research** 