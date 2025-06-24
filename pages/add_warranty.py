import streamlit as st
from app import add_warranty_item, validate_dates, CATEGORIES,generate_warranty_pdf,check_expiring_warranties

if st.session_state.get("logged_in"):
    cols = st.columns([1,1,1,1,1,1])
    with cols[0]:
        if st.button("🏠 Home"):
            st.switch_page("app.py")
    with cols[1]:
        if st.button("➕ Add Warranty"):
            st.rerun()
    with cols[2]:
        if st.button("📋 View Warranties"):
            st.switch_page("pages/warranties.py")
    with cols[3]:
        if st.button("📑 Export PDF"):
            pdf_bytes = generate_warranty_pdf()
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name="warranty_report.pdf",
                mime="application/pdf",
                key="navbar_pdf"
            )
    with cols[4]:
        if st.button("📧 Mail Report"):
            check_expiring_warranties()
    with cols[5]:
        if st.button("📤 Logout"):
            st.session_state.clear()
            st.rerun()
    st.markdown("---")

st.title("Add New Warranty")

if not st.session_state.get("logged_in"):
    st.warning("Please login to add warranties")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login Now", use_container_width=True):
            st.switch_page("pages/login.py")
    with col2:
        if st.button("Sign Up", use_container_width=True):
            st.switch_page("pages/signup.py")
    st.stop()

with st.form("warranty_form"):
    item_name = st.text_input("Item Name*")
    col1,col2 = st.columns(2)
    category = st.selectbox("Category*", CATEGORIES)
    with col1:
        purchase_date = st.date_input("Purchase Date*")
    with col2:
        warranty_end_date = st.date_input("Warranty End Date*")
    warranty_image = st.file_uploader("Warranty Card Image*", type=['png', 'jpg', 'jpeg'])
    description = st.text_area("Description (Optional)")
    submitted = st.form_submit_button("Add Warranty")

    if submitted:
        if not item_name:
            st.error("Please enter item name")
        elif not category:
            st.error("Please select a category")
        elif not warranty_image:
            st.error("Please upload warranty card image")
        elif not validate_dates(purchase_date, warranty_end_date):
            st.error("Warranty end date must be after purchase date")
        else:
            image_bytes = warranty_image.read() if warranty_image else None
            add_warranty_item(
                st.session_state.user_id,
                item_name, category, purchase_date, 
                warranty_end_date, image_bytes, description
            )
            st.success("Warranty added successfully!")
