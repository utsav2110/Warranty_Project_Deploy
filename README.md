# 🔔 Warranty Management System

A comprehensive web application for managing product warranties built with Streamlit and PostgreSQL.

## ⭐ Features

- 👤 User Authentication & Authorization
  - Secure login/signup with email verification
  - Role-based access (Admin/User)
  - Password recovery system

- 📝 Warranty Management
  - Add warranties with images
  - Track expiry dates
  - Categorize items
  - Search and filter warranties

- 📊 Analytics & Reports
  - Category distribution charts
  - Expiry timeline visualization
  - PDF report generation
  - Email notifications for expiring warranties

- 👑 Admin Dashboard
  - User management
  - System-wide warranty overview
  - Usage statistics
  - Data visualization

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- SMTP server access (for email notifications)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database:
```sql
CREATE DATABASE db_name;
```

3. Configure email settings in `app.py`:
```python
sender_email = "your-email@gmail.com"
sender_password = "your-app-password"
```

4. Run the application:
```bash
streamlit run app.py
```

## 💻 Tech Stack

- 🎯 Streamlit - Web framework
- 🐘 PostgreSQL - Database
- 📧 SMTP - Email notifications
- 📊 Plotly - Data visualization
- 📄 FPDF - PDF generation

## 🔒 Security Features

- Password hashing with bcrypt
- Email verification
- Session management
- OTP system for password recovery
- Role-based access control

## 🎨 UI Components

- Responsive navigation
- Interactive charts
- Grid view for warranties
- Image preview
- Form validation
- Toast notifications