import streamlit as st
import psycopg
import bcrypt
import re
import random
import smtplib
import time
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse
from datetime import datetime, timedelta
from PIL import Image
from fpdf import FPDF
import io
import os
from email.mime.application import MIMEApplication
import plotly.express as px

CATEGORIES = [
    "Electronics", "Appliances", "Vehicles", "Furniture", 
    "Tools", "Mobile Devices", "Computers", "Other"
]

def add_warranty_item(user_id, item_name, category, purchase_date, warranty_end_date, warranty_image, description):
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute(
        """INSERT INTO warranty_items (user_id, item_name, category, purchase_date, warranty_end_date, warranty_card_image, description)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (user_id, item_name, category, purchase_date, warranty_end_date, warranty_image, description)
    )
    
    conn.commit()
    cur.close()
    conn.close()

def get_all_warranties():
    if not st.session_state.get("logged_in") or st.session_state.get("role") == "admin":
        return []
    
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM warranty_items 
        WHERE user_id = %s 
        ORDER BY warranty_end_date
    """, (st.session_state.get("user_id"),))
    items = cur.fetchall()
    cur.close()
    conn.close()
    return items

def search_warranties(search_term="", category=None, date_filter=None):
    if not st.session_state.get("logged_in") or st.session_state.get("role") == "admin":
        return []
    
    conn = get_conn()
    cur = conn.cursor()
    
    query = "SELECT * FROM warranty_items WHERE user_id = %s"
    params = [st.session_state.get("user_id")]
    
    if search_term:
        query += " AND (item_name ILIKE %s OR description ILIKE %s)"
        search_pattern = f"%{search_term}%"
        params.extend([search_pattern, search_pattern])
    
    if category and category != "All":
        query += " AND category = %s"
        params.append(category)
    
    if date_filter == "Expiring Soon":
        query += " AND warranty_end_date <= %s"
        params.append((datetime.now() + timedelta(days=7)).date())
    
    query += " ORDER BY warranty_end_date"
    
    cur.execute(query, params)
    items = cur.fetchall()
    cur.close()
    conn.close()
    return items

def validate_dates(purchase_date, warranty_end_date):
    if warranty_end_date <= purchase_date:
        return False
    return True

def get_user_email(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT email FROM users WHERE user_id = %s", (user_id,))
    email = cur.fetchone()
    cur.close()
    conn.close()
    return email[0] if email else None

def check_expiring_warranties():
    user_id = st.session_state.get("user_id")
    user_email = get_user_email(user_id)
    
    if not user_email:
        st.error("Could not find user email.")
        return
    
    sender = st.secrets["email"]["sender"]
    password = st.secrets["email"]["password"]
    
    warranties = get_all_warranties()
    if not warranties:
        st.warning("No warranties found to send.")
        return
    
    email_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: #2c3e50;">Your Warranty Report</h1>
            <p style="color: #7f8c8d;">Complete list of your registered warranties</p>
        </div>
        <div style="padding: 20px; background-color: white; border-radius: 0 0 10px 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h2 style="color: #3498db;">Warranty Summary</h2>
            <p>Total Warranties: {len(warranties)}</p>
            <div style="margin: 20px 0;">
                <h3 style="color: #2c3e50;">Warranty List:</h3>
                <ul style="list-style-type: none; padding: 0;">
    """
    
    for warranty in warranties:
        email_body += f"""
            <li style="margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-radius: 5px;">
                <strong style="color: #2c3e50;">{warranty[2]}</strong><br>
                Category: {warranty[3]}<br>
                Expires: {warranty[5]}
            </li>
        """
    
    email_body += """
                </ul>
            </div>
        </div>
        <div style="text-align: center; margin-top: 20px; color: #7f8c8d;">
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </div>
    """
    
    pdf_bytes = generate_warranty_pdf()
        
    try:
        msg = MIMEMultipart("alternative")
        msg['Subject'] = 'Complete Warranty Report'
        msg['From'] = f"Warranty System <{sender}>"
        msg['To'] = user_email
        
        msg.attach(MIMEText(email_body, 'html'))
        
        pdf_attachment = MIMEApplication(pdf_bytes, _subtype='pdf')
        pdf_attachment.add_header('Content-Disposition', 'attachment',  filename='warranty_report.pdf')
        msg.attach(pdf_attachment)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, user_email, msg.as_string())
            
        st.success("Complete warranty report sent to your email!")
            
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")

def generate_warranty_pdf():
    warranties = get_all_warranties()
    pdf = FPDF()
    
    for warranty in warranties:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f'Item: {warranty[2]}', ln=True)  
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Category: {warranty[3]}', ln=True)  
        pdf.cell(0, 10, f'Purchase Date: {warranty[4]}', ln=True)  
        pdf.cell(0, 10, f'Warranty End Date: {warranty[5]}', ln=True)  
        pdf.cell(0, 10, f'Description: {warranty[7]}', ln=True)  
        
        if warranty[6]:  
            try:
                image = Image.open(io.BytesIO(warranty[6]))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                    
                img_path = f"temp_{warranty[0]}.jpg"
                image.save(img_path, 'JPEG', quality=85)
                
                try:
                    pdf.image(img_path, x=10, y=100, w=190)
                finally:
                    if os.path.exists(img_path):
                        os.remove(img_path)
            except Exception as e:
                pdf.cell(0, 10, f"Error including warranty image: {str(e)}", ln=True)
    
    return pdf.output(dest='S').encode('latin1')

def send_email(to_email, subject, body):
    sender_email = st.secrets["email"]["sender"]
    sender_password = st.secrets["email"]["password"]
    
    message = MIMEMultipart("alternative")
    message["From"] = f"Authentication System <{sender_email}>"
    message["To"] = to_email
    message["Subject"] = subject
    
    html_content = get_email_template(subject, body)
    message.attach(MIMEText(body, "plain"))  
    message.attach(MIMEText(html_content, "html"))  
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

def get_email_template(subject, content):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ padding: 20px; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
            .button {{ display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{subject}</h2>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                <p>This is an automated message, please do not reply to this email.</p>
                <p>If you did not request this, please ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

def generate_otp():
    return {
        'code': str(random.randint(100000, 999999)),
        'expiry': time.time() + 600 
    }

def get_conn():
    return psycopg.connect(
        host=st.secrets["postgres"]["host"],
        port=st.secrets["postgres"]["port"],
        dbname=st.secrets["postgres"]["database"], 
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        sslmode="require"  
    )

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def signup_user(username, email, password, confirm_password):
    if password != confirm_password:
        st.warning("Passwords do not match.")
        return False
    
    if len(password) < 6:
        st.warning("Password should be at least 6 characters.")
        return False
    
    if not is_valid_email(email):
        st.warning("Invalid email format.")
        return False

    otp = generate_otp()
    email_content = f"""
    <p>Hello {username},</p>
    <p>Thank you for signing up! Please use the following OTP to verify your email address:</p>
    <h1 style="text-align: center; color: #007bff; font-size: 36px; letter-spacing: 5px;">{otp['code']}</h1>
    <p>This code will expire in 10 minutes.</p>
    <p>For security reasons, please do not share this code with anyone.</p>
    """
    if send_email(email, "Email Verification", email_content):
        st.session_state['temp_user'] = {
            'username': username,
            'email': email,
            'password': password,
            'otp': otp
        }
        return True
    return False

def verify_otp(entered_otp):
    if 'temp_user' not in st.session_state:
        return False, "Session expired"
    
    stored_otp = st.session_state['temp_user']['otp']
    
    if time.time() > stored_otp['expiry']:
        del st.session_state['temp_user']
        return False, "OTP has expired"
    
    if entered_otp == stored_otp['code']:
        user = st.session_state['temp_user']
        hashed = bcrypt.hashpw(user['password'].encode(), bcrypt.gensalt()).decode()
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
            """, (user['username'], user['email'], hashed))
            conn.commit()
            cur.close()
            conn.close()
            del st.session_state['temp_user']
            return True, "Success"
        except Exception as e:
            return False, f"Signup failed: {e}"
    return False, "Invalid OTP"

def login_user(username, password):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id, password_hash, role 
            FROM users 
            WHERE username = %s OR email = %s
        """, (username, username))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return False, None, "User not found"
        
        if not bcrypt.checkpw(password.encode(), row[1].encode()):
            return False, None, "Incorrect password"
        
        st.session_state["user_id"] = row[0]  
        return True, row[2], None
    except Exception as e:
        st.error(f"Login failed: {e}")
        return False, None, str(e)

def check_username_exists(username):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except Exception:
        return False

def check_email_exists(email):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE email = %s", (email,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except Exception:
        return False

def validate_password(password):
    if len(password) < 6:
        return "Password must be at least 6 characters"
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number"
    return None

def get_category_stats():
    warranties = get_all_warranties()
    category_counts = {}
    for warranty in warranties:
        category = warranty[3]
        category_counts[category] = category_counts.get(category, 0) + 1
    return category_counts

def get_expiry_timeline():
    warranties = get_all_warranties()
    today = datetime.now().date()
    timelines = {
        "Expired": 0,
        "This Week": 0,
        "This Month": 0,
        "3 Months": 0,
        "6 Months": 0,
        "Later": 0
    }
    
    for warranty in warranties:
        expiry_date = warranty[5]
        days_until = (expiry_date - today).days
        
        if days_until < 0:
            timelines["Expired"] += 1
        elif days_until <= 7:
            timelines["This Week"] += 1
        elif days_until <= 30:
            timelines["This Month"] += 1
        elif days_until <= 90:
            timelines["3 Months"] += 1
        elif days_until <= 180:
            timelines["6 Months"] += 1
        else:
            timelines["Later"] += 1
            
    return timelines

def get_current_route():
    try:
        query_params = st.query_params
        page = query_params.get("page", "home")
        path = urlparse(page).path
        return path
    except:
        return "home"

def navigate_to(page):
    st.query_params['page'] = page

def get_data_as_df(query):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query)
    data = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return pd.DataFrame(data, columns=columns)

st.set_page_config(page_title="Warranty Expiry Tracking System", page_icon="🔐", layout="wide")

with st.container():
    if not st.session_state.get("logged_in"):
        cols = st.columns([1,1,1,1,1])
        with cols[0]:
            if st.button("🏠 Home"):
                st.query_params['page'] = 'home'
                st.rerun()
        with cols[1]:
            if st.button("👤 Login"):
                st.switch_page("pages/login.py")
        with cols[2]:
            if st.button("📝 Sign Up"):
                st.switch_page("pages/signup.py")
        with cols[3]:
            if st.button("🔑 Forgot Password"):
                st.switch_page("pages/forgot_password.py")
    else:
        if st.session_state["role"] == "admin":
            cols = st.columns([1,1,1])
            with cols[0]:
                if st.button("🏠 Home"):
                    st.query_params['page'] = 'home'
                    st.rerun()
            with cols[1]:
                if st.button("👑 Dashboard"):
                    st.switch_page("pages/admin_dashboard.py")
            with cols[2]:
                if st.button("📤 Logout"):
                    st.session_state.clear()
                    st.rerun()
        else:
            cols = st.columns([1,1,1,1])
            with cols[0]:
                if st.button("🏠 Home"):
                    st.query_params['page'] = 'home'
                    st.rerun()
            with cols[1]:
                if st.button("➕ Add Warranty"):
                    st.switch_page("pages/add_warranty.py")
            with cols[2]:
                if st.button("📋 View Warranties"):
                    st.switch_page("pages/warranties.py")
            with cols[3]:
                if st.button("📤 Logout"):
                    st.session_state.clear()
                    st.rerun()

st.markdown("---")

st.title("Welcome to Warranty Management System")
if st.session_state.get("logged_in"):
    st.info(f"Logged in as: {st.session_state['username']}")
    
    if st.session_state["role"] == "admin":
        st.warning("Admin users don't have access to warranty management features.")
        
        st.subheader("👥 All Registered Users")
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT user_id, username, email, role, created_at FROM users")
            users = cur.fetchall()
            cur.close()
            conn.close()

            df = pd.DataFrame(users, columns=["ID", "Username", "Email", "Role", "Created At"])
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error fetching users: {e}")

        st.subheader("📜 Warranty Items Overview")
        try:
            warranties_query = """
                SELECT 
                    w.id as "ID",
                    u.username as "Owner",
                    w.item_name as "Item",
                    w.category as "Category",
                    to_char(w.purchase_date, 'YYYY-MM-DD') as "Purchase Date",
                    to_char(w.warranty_end_date, 'YYYY-MM-DD') as "Expiry Date",
                    to_char(w.created_at, 'YYYY-MM-DD HH24:MI') as "Created At"
                FROM warranty_items w
                JOIN users u ON w.user_id = u.user_id
                ORDER BY w.created_at DESC
            """
            warranties_df = get_data_as_df(warranties_query)
            st.dataframe(warranties_df, use_container_width=True)
        except Exception as e:
            st.error(f"Error fetching warranties: {e}")

    else:

        st.success("🎯 Welcome to Your Warranty Dashboard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Category Distribution")
            category_stats = get_category_stats()
            if category_stats:
                fig = px.pie(
                    values=list(category_stats.values()),
                    names=list(category_stats.keys()),
                    hole=0.3
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Add warranties to see category distribution")
                
        with col2:
            st.subheader("⏳ Expiry Timeline")
            timeline_stats = get_expiry_timeline()
            if any(timeline_stats.values()):
                fig = px.bar(
                    x=list(timeline_stats.keys()),
                    y=list(timeline_stats.values()),
                    labels={'x': 'Timeline', 'y': 'Number of Warranties'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Add warranties to see expiry timeline")
        
        st.subheader("📈 Quick Stats")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_warranties = len(get_all_warranties())
            st.metric("Total Warranties", total_warranties)
        with col2:
            expiring_soon = len(search_warranties(date_filter="Expiring Soon"))
            st.metric("Expiring Soon", expiring_soon)
        with col3:
            active_categories = len(get_category_stats())
            st.metric("Active Categories", active_categories)
        
        st.subheader("🆕 Recent Warranties")
        recent = search_warranties()[:3]
        if recent:
            cols = st.columns(3)
            for idx, warranty in enumerate(recent):
                with cols[idx]:
                    with st.container():
                        st.markdown("""
                        <style>
                            .warranty-card {
                                padding: 1rem;
                                border-radius: 0.5rem;
                                border: 1px solid #ddd;
                                margin: 0.5rem 0;
                            }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        <div class="warranty-card">
                            <h3>{warranty[2]}</h3>
                            <p><strong>Category:</strong> {warranty[3]}</p>
                            <p><strong>Expires:</strong> {warranty[5]}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if warranty[6]: 
                            try:
                                image = Image.open(io.BytesIO(warranty[6]))
                                if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                                    image = image.convert('RGBA')
                                else:
                                    image = image.convert('RGB')
                                st.image(image, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error loading image: {str(e)}")
                                
                        if st.button("View Details", key=f"view_{warranty[0]}"):
                            st.session_state.selected_warranty = warranty[0]
                            st.switch_page("pages/warranty_details.py")
        else:
            st.info("No warranties added yet. Click 'Add Warranty' to get started!")
else:
    st.write("Please login to access your warranty dashboard.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login Now", use_container_width=True):
            st.switch_page("pages/login.py")
    with col2:
        if st.button("Sign Up", use_container_width=True):
            st.switch_page("pages/signup.py")
