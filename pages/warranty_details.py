import streamlit as st
from app import get_conn, Image, io , generate_warranty_pdf,check_expiring_warranties

def get_warranty_by_id(warranty_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM warranty_items 
        WHERE id = %s AND user_id = %s
    """, (warranty_id, st.session_state.get("user_id")))
    warranty = cur.fetchone()
    cur.close()
    conn.close()
    return warranty

if st.session_state.get("logged_in"):
    cols = st.columns([1,1,1,1,1,1])
    with cols[0]:
        if st.button("🏠 Home"):
            st.switch_page("app.py")
    with cols[1]:
        if st.button("➕ Add Warranty"):
            st.switch_page("pages/add_warranty.py")
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

if not st.session_state.get("logged_in"):
    st.warning("Please login to view warranty details")
    st.stop()

warranty_id = st.session_state.get("selected_warranty")
if not warranty_id:
    st.error("No warranty selected")
    st.stop()

warranty = get_warranty_by_id(warranty_id)
if not warranty:
    st.error("Warranty not found")
    st.stop()

st.title(warranty[2])  

col1, col2 = st.columns([2,1])
with col1:
    if warranty[6]: 
        try:
            image = Image.open(io.BytesIO(warranty[6]))
            st.image(image, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading image: {str(e)}")
            
with col2:
    st.write("### Details")
    st.write(f"**Category:** {warranty[3]}")
    st.write(f"**Purchase Date:** {warranty[4]}")
    st.write(f"**Warranty End Date:** {warranty[5]}")
    st.write("### Description")
    st.write(warranty[7] or "No description provided")
