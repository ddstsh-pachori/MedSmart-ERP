import os
import io
import time
import datetime
import re
import urllib.parse
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fpdf import FPDF

# ==============================================================================
# 1. PAGE SETUP & RAINBOW BUTTON CSS TARGETING
# ==============================================================================
st.set_page_config(
    page_title="MedSmart ERP",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .block-container { 
        padding-top: 2.5rem; 
        padding-bottom: 2rem; 
    }
    .banner-container {
        margin-top: 10px;
        margin-bottom: 25px;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .main-title { font-size: 32px; font-weight: 700; color: #0F172A; margin-bottom: 2px; }
    .sub-title { font-size: 14px; color: #475569; margin-bottom: 20px; }
    
    /* RAINBOW BUTTON CARDS (TARGETING MULTIPLE STREAMLIT DOM VERSIONS) */
    div.stButton > button,
    div[data-testid="stButton"] > button {
        height: 105px !important;
        min-height: 105px !important;
        padding: 14px 12px !important;
        border-radius: 12px !important;
        border: none !important;
        color: #ffffff !important;
        text-align: left !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: flex-start !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.12) !important;
    }
    
    div.stButton > button:hover,
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 18px rgba(0,0,0,0.22) !important;
    }
    
    div.stButton > button:focus,
    div[data-testid="stButton"] > button:focus {
        outline: none !important;
        border: none !important;
    }

    div.stButton > button p,
    div.stButton > button div,
    div[data-testid="stButton"] > button p {
        margin: 0 !important;
        line-height: 1.3 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        white-space: pre-line !important;
    }

    /* 1. Red Coral */
    div[data-testid="stColumn"]:nth-child(1) div.stButton > button,
    div[data-testid="column"]:nth-child(1) div.stButton > button {
        background: linear-gradient(135deg, #FF416C, #FF4B2B) !important;
    }

    /* 2. Amber Orange */
    div[data-testid="stColumn"]:nth-child(2) div.stButton > button,
    div[data-testid="column"]:nth-child(2) div.stButton > button {
        background: linear-gradient(135deg, #FF8008, #FFC837) !important;
    }

    /* 3. Emerald Green */
    div[data-testid="stColumn"]:nth-child(3) div.stButton > button,
    div[data-testid="column"]:nth-child(3) div.stButton > button {
        background: linear-gradient(135deg, #11998E, #38EF7D) !important;
    }

    /* 4. Deep Cyan / Ocean Blue */
    div[data-testid="stColumn"]:nth-child(4) div.stButton > button,
    div[data-testid="column"]:nth-child(4) div.stButton > button {
        background: linear-gradient(135deg, #00C6FF, #0072FF) !important;
    }

    /* 5. Violet / Deep Purple */
    div[data-testid="stColumn"]:nth-child(5) div.stButton > button,
    div[data-testid="column"]:nth-child(5) div.stButton > button {
        background: linear-gradient(135deg, #8A2387, #E94057) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. STATE PERSISTENCE & INITIALIZATION
# ==============================================================================
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.dashboard_view = None
    st.session_state.patients = [
        {"uhid": "UHID-2026-001", "name": "Aman Verma", "age": 42, "gender": "Male", "mobile": "9876543210", "blood": "O+", "alerts": "Penicillin Allergy", "registration_fee": 500.0},
        {"uhid": "UHID-2026-002", "name": "Meera Nair", "age": 35, "gender": "Female", "mobile": "9123456789", "blood": "A-", "alerts": "None", "registration_fee": 500.0}
    ]
    st.session_state.surgeries = [
        {"id": "SURG-101", "uhid": "UHID-2026-001", "patient": "Aman Verma", "procedure": "Laparoscopic Cholecystectomy", "surgeon": "Dr. Prateek", "date": datetime.date.today(), "status": "Scheduled", "ot": "OT-1"},
        {"id": "SURG-102", "uhid": "UHID-2026-002", "patient": "Meera Nair", "procedure": "Appendectomy", "surgeon": "Dr. Prateek", "date": datetime.date.today(), "status": "Completed", "ot": "OT-2"}
    ]
    st.session_state.billing = [
        {"invoice": "INV-2026-001", "uhid": "UHID-2026-001", "patient": "Aman Verma", "amount": 75000.0, "status": "Pending", "date": datetime.date.today()},
        {"invoice": "INV-2026-002", "uhid": "UHID-2026-002", "patient": "Meera Nair", "amount": 45000.0, "status": "Paid", "date": datetime.date.today()}
    ]
    st.session_state.inventory = [
        {"item": "Surgical Gloves 7.5", "type": "Consumables", "stock": 120, "min_level": 50},
        {"item": "Vicryl 2-0 Sutures", "type": "Sutures", "stock": 15, "min_level": 30},
        {"item": "Titanium Mesh", "type": "Implants", "stock": 8, "min_level": 5}
    ]

# Core System Targets
ADMIN_EMAIL = "ddstsh@gmail.com"
ADMIN_WHATSAPP = "917000768168"
SENDER_EMAIL = "ddstsh@gmail.com"
SENDER_PASSWORD = "zfceifhtgngjehgz"

# Green-API Configuration
GREEN_API_INSTANCE_ID = "710722686373"
GREEN_API_TOKEN = "2cfa62d49de84c8f845396d2d69619234895a8d28be3413799"

# ==============================================================================
# 3. BANNER RESOLUTION & DISPATCH ENGINES
# ==============================================================================
def find_banner_image():
    priority_files = [
        "MedSmart_ERP_Large_Banner_4K.jpg",
        "medsmart_banner.jpg",
        "medsmart banner.png",
        "medsmart_banner.png",
        "medsmart_banner.png.png",
        "medsmart_poster.jpeg",
        "niramaya.jpg.jpeg",
        "niramaya.jpg"
    ]
    for p in priority_files:
        if os.path.exists(p):
            return p
            
    for f in os.listdir('.'):
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            return f
    return None

def send_whatsapp_message(mobile_number: str, message_text: str):
    clean_phone = re.sub(r"\D", "", mobile_number)
    if len(clean_phone) == 10:
        clean_phone = "91" + clean_phone
    chat_id = f"{clean_phone}@c.us"
    url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE_ID}/sendMessage/{GREEN_API_TOKEN}"
    try:
        res = requests.post(url, json={"chatId": chat_id, "message": message_text}, timeout=8)
        return res.status_code == 200, res.text
    except Exception as e:
        return False, str(e)

def send_whatsapp_pdf(mobile_number: str, pdf_bytes: bytes, file_name: str, caption: str = ""):
    clean_phone = re.sub(r"\D", "", mobile_number)
    if len(clean_phone) == 10:
        clean_phone = "91" + clean_phone
    chat_id = f"{clean_phone}@c.us"
    url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE_ID}/sendFileByUpload/{GREEN_API_TOKEN}"
    try:
        res = requests.post(
            url,
            data={'chatId': chat_id, 'fileName': file_name, 'caption': caption},
            files=[('file', (file_name, pdf_bytes, 'application/pdf'))],
            timeout=12
        )
        return res.status_code == 200, res.text
    except Exception as e:
        return False, str(e)

def compile_and_dispatch(label, df, target_email=None, target_whatsapp=None):
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='MedSmart Data', index=False)
    excel_data = excel_buffer.getvalue()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "MedSmart ERP - Surgical Clinic", ln=True, align="L")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Report Profile: {label.replace('_', ' ')}", ln=True, align="L")
    pdf.cell(0, 7, f"Date: {datetime.date.today().strftime('%Y-%m-%d')}", ln=True, align="L")
    pdf.ln(6)
    
    num_cols = len(df.columns)
    c_width = 190 / max(num_cols, 1)
    
    pdf.set_font("Helvetica", "B", 8)
    for col in df.columns:
        pdf.cell(c_width, 7, str(col)[:18], border=1)
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 7)
    for _, row in df.iterrows():
        for val in row:
            pdf.cell(c_width, 6, str(val)[:22], border=1)
        pdf.ln()
        
    pdf_data = bytes(pdf.output())
    
    email_success = False
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"[MedSmart ERP] {label}"
        msg['From'] = SENDER_EMAIL
        recipients = [ADMIN_EMAIL]
        if target_email and target_email.strip():
            recipients.append(target_email.strip())
        msg['To'] = ", ".join(recipients)
        msg.attach(MIMEText(f"Attached is the requested system statement ({label}).\n\nMedSmart ERP Automated System", 'plain'))
        
        part_xl = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        part_xl.set_payload(excel_data)
        encoders.encode_base64(part_xl)
        part_xl.add_header('Content-Disposition', f'attachment; filename={label}.xlsx')
        msg.attach(part_xl)
        
        part_pdf = MIMEBase('application', 'pdf')
        part_pdf.set_payload(pdf_data)
        encoders.encode_base64(part_pdf)
        part_pdf.add_header('Content-Disposition', f'attachment; filename={label}.pdf')
        msg.attach(part_pdf)
        
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=6)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        server.quit()
        email_success = True
    except Exception as e:
        email_err = str(e)
        
    caption = f"📄 *MedSmart ERP - {label.replace('_', ' ')}*\nDate: {datetime.date.today().strftime('%d/%m/%Y')}"
    send_whatsapp_pdf(ADMIN_WHATSAPP, pdf_data, f"{label}.pdf", caption)
    if target_whatsapp and target_whatsapp.strip():
        send_whatsapp_pdf(target_whatsapp, pdf_data, f"{label}.pdf", caption)
        
    if email_success:
        return True, "Dispatched successfully via Email and WhatsApp!"
    return False, f"WhatsApp dispatched. Email alert: {email_err}"

# ==============================================================================
# 4. UPPER WIDESCREEN BANNER
# ==============================================================================
banner_file = find_banner_image()
if banner_file:
    st.markdown('<div class="banner-container">', unsafe_allow_html=True)
    st.image(banner_file, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 5. SIDEBAR NAVIGATION & ROUTING
# ==============================================================================
with st.sidebar:
    st.markdown("### **MedSmart ERP Gateway**")
    selected_role = st.selectbox("System Access Node", ["Admin", "Surgeon", "Receptionist", "Nurse", "Accountant"], index=0)
    
    nav_opts = [
        "🖥️ Live Executive Dashboard",
        "📋 Patient Identity Registration",
        "🩺 Outpatient & Searchable EMR",
        "🔪 Surgical Suite & OT",
        "💳 Medical Billing Ledger",
        "📦 Medical Pharmacy & Inventory",
        "📊 Consolidated System Reports"
    ]
    module_selection = st.radio("Active ERP Core Module", nav_opts)

st.markdown('<div class="main-title">MedSmart ERP</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">Paperless Healthcare System — Active Context: <b>{selected_role} Node</b> ({module_selection})</div>', unsafe_allow_html=True)
st.write("---")

# ==============================================================================
# MODULE 1: LIVE EXECUTIVE DASHBOARD (RAINBOW THEMED BUTTONS)
# ==============================================================================
if "🖥️ Live Executive Dashboard" in module_selection:
    st.subheader("Real-Time Clinical Operations Center")
    
    total_patients = len(st.session_state.patients)
    total_surgeries = len(st.session_state.surgeries)
    total_inventory_items = sum([int(i.get("stock", 0)) for i in st.session_state.inventory])
    total_rev = sum([float(b.get("amount", 0)) for b in st.session_state.billing])
    low_stock_items = [i for i in st.session_state.inventory if int(i.get("stock", 0)) <= int(i.get("min_level", 0))]
    low_stock_count = len(low_stock_items)
    
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        if st.button(f"Registered Patients\n\n{total_patients} Intake", use_container_width=True):
            st.session_state.dashboard_view = 'patients'
    with m2:
        if st.button(f"Surgeries Scheduled\n\n{total_surgeries} Procedures", use_container_width=True):
            st.session_state.dashboard_view = 'surgeries'
    with m3:
        if st.button(f"Inventory Stock Units\n\n{total_inventory_items} Units", use_container_width=True):
            st.session_state.dashboard_view = 'inventory'
    with m4:
        if st.button(f"Net Ledger Revenue\n\n₹{total_rev:,.0f}", use_container_width=True):
            st.session_state.dashboard_view = 'billing'
    with m5:
        if st.button(f"Low Stock Alerts\n\n{low_stock_count} Items", use_container_width=True):
            st.session_state.dashboard_view = 'alerts'

    # Display Underlying Data on Card Click
    if st.session_state.dashboard_view:
        with st.expander(f"Detailed Data View: {st.session_state.dashboard_view.upper().replace('_', ' ')}", expanded=True):
            if st.session_state.dashboard_view == 'patients':
                st.dataframe(pd.DataFrame(st.session_state.patients), use_container_width=True)
            elif st.session_state.dashboard_view == 'surgeries':
                st.dataframe(pd.DataFrame(st.session_state.surgeries), use_container_width=True)
            elif st.session_state.dashboard_view == 'inventory':
                st.dataframe(pd.DataFrame(st.session_state.inventory), use_container_width=True)
            elif st.session_state.dashboard_view == 'billing':
                st.dataframe(pd.DataFrame(st.session_state.billing), use_container_width=True)
            elif st.session_state.dashboard_view == 'alerts':
                if low_stock_count > 0:
                    st.warning("The following items require immediate restock:")
                    st.dataframe(pd.DataFrame(low_stock_items), use_container_width=True)
                else:
                    st.success("All inventory items are currently well-stocked above thresholds.")
            
            if st.button("✖️ Close Data View", key="close_view"):
                st.session_state.dashboard_view = None
                st.rerun()
                
    st.write("---")
    st.markdown("### Interactive Visual Analytics Studio")
    
    df_rev = pd.DataFrame({"Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], "Revenue": [45000, 78000, 120500, 91000, 62000, 110000]})
    df_surg = pd.DataFrame({"Category": ["General", "Orthopedic", "Laparoscopic", "Urology"], "Count": [12, 5, 22, 8]})
    
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("#### Revenue Inflow Trends")
        rev_choice = st.selectbox("Select Chart Format", ["Line Chart", "Bar Chart", "Area Chart"], key="rev_chart")
        if rev_choice == "Line Chart":
            fig1 = px.line(df_rev, x="Day", y="Revenue", markers=True, color_discrete_sequence=['#3B82F6'])
        elif rev_choice == "Bar Chart":
            fig1 = px.bar(df_rev, x="Day", y="Revenue", color="Revenue", color_continuous_scale="Blues")
        else:
            fig1 = px.area(df_rev, x="Day", y="Revenue", color_discrete_sequence=['#3B82F6'])
        st.plotly_chart(fig1, use_container_width=True)
        
    with g2:
        st.markdown("#### Surgical Department Volume")
        surg_choice = st.selectbox("Select Chart Format", ["Donut Chart", "Pie Chart", "Bar Chart", "Funnel Chart"], key="surg_chart")
        if surg_choice == "Donut Chart":
            fig2 = px.pie(df_surg, names="Category", values="Count", hole=0.5, color_discrete_sequence=px.colors.qualitative.Prism)
        elif surg_choice == "Pie Chart":
            fig2 = px.pie(df_surg, names="Category", values="Count", color_discrete_sequence=px.colors.qualitative.Prism)
        elif surg_choice == "Bar Chart":
            fig2 = px.bar(df_surg, x="Category", y="Count", color="Category", color_discrete_sequence=px.colors.qualitative.Vivid)
        else:
            fig2 = px.funnel(df_surg, x="Count", y="Category")
        st.plotly_chart(fig2, use_container_width=True)

# ==============================================================================
# MODULE 2: PATIENT IDENTITY REGISTRATION
# ==============================================================================
elif "📋 Patient Identity Registration" in module_selection:
    st.subheader("New Patient Intake Processing Platform")
    
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        p_name = st.text_input("Full Patient Name", placeholder="e.g. Rahul Sharma")
        p_age = st.number_input("Age", min_value=0, max_value=125, value=30)
        p_gender = st.radio("Gender", ["Male", "Female", "Other"], horizontal=True)
        p_mobile = st.text_input("Mobile / WhatsApp Number", value="+91")
    with f_col2:
        p_blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        p_alerts = st.text_area("Critical Medical Alerts & Allergies", value="None")
        p_reg_fee = st.number_input("Intake Fee (INR)", min_value=0, value=500, step=50)
        p_email = st.text_input("Email ID (For PDF Receipt)", placeholder="patient@domain.com")
    
    if st.button("Generate System UHID & Send Dual-Dispatch", use_container_width=True, type="primary"):
        clean_phone = re.sub(r"\D", "", p_mobile)
        if p_name.strip() and clean_phone:
            new_uhid = f"UHID-2026-00{len(st.session_state.patients) + 1}"
            patient_record = {
                "uhid": new_uhid, "name": p_name, "age": p_age, "gender": p_gender,
                "mobile": p_mobile, "blood": p_blood, "alerts": p_alerts,
                "registration_fee": float(p_reg_fee)
            }
            st.session_state.patients.append(patient_record)
            
            df_receipt = pd.DataFrame([{
                "UHID": new_uhid,
                "Patient Name": p_name,
                "Age/Gender": f"{p_age}/{p_gender}",
                "Mobile": p_mobile,
                "Blood Group": p_blood,
                "Fee": f"INR {p_reg_fee}",
                "Date": datetime.date.today().strftime("%Y-%m-%d")
            }])
            
            with st.spinner("Dispatching Dual-Format records via Email and WhatsApp..."):
                status_flag, return_message = compile_and_dispatch(
                    f"Intake_Receipt_{new_uhid}",
                    df_receipt,
                    target_email=p_email,
                    target_whatsapp=p_mobile
                )
                
            wa_text = (
                f"*MEDSMART ERP - Intake Receipt*\n\n"
                f"👤 *Patient:* {p_name}\n"
                f"🆔 *UHID:* {new_uhid}\n"
                f"🩸 *Blood Group:* {p_blood}\n"
                f"💰 *Fee Paid:* ₹{p_reg_fee}\n"
                f"📅 *Date:* {datetime.date.today().strftime('%d/%m/%Y')}\n\n"
                f"Your registration file has been generated."
            )
            send_whatsapp_message(p_mobile, wa_text)
            
            if status_flag:
                st.success(f"✅ {new_uhid} registered! {return_message}")
            else:
                st.warning(return_message)
                
            fallback_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(wa_text)}"
            st.markdown(
                f"""
                <a href="{fallback_url}" target="_blank" style="
                    display: flex; align-items: center; justify-content: center;
                    width: 100%; background-color: #25D366; color: #ffffff !important;
                    font-size: 15px; font-weight: 600; padding: 10px 0; border-radius: 6px;
                    text-decoration: none !important; margin-top: 10px;
                ">
                    📲 Open in WhatsApp Web / App (+{clean_phone})
                </a>
                """,
                unsafe_allow_html=True
            )
            time.sleep(2)
            st.rerun()
        else:
            st.error("Please enter patient name and valid mobile number.")
            
    st.write("---")
    st.markdown("#### Registered Clinic Patient Demographics Manifest")
    st.dataframe(pd.DataFrame(st.session_state.patients), use_container_width=True)

# ==============================================================================
# MODULE 3: OUTPATIENT & EMR
# ==============================================================================
elif "🩺 Outpatient & Searchable EMR" in module_selection:
    st.subheader("Searchable EMR & Patient Vitals Intake System")
    patient_search_list = [f"{p['uhid']} - {p['name']}" for p in st.session_state.patients]
    selected_search_target = st.selectbox("Search Patient Record Base", patient_search_list)
    target_uhid = selected_search_target.split(" - ")[0]
    patient_record_dict = next(p for p in st.session_state.patients if p["uhid"] == target_uhid)
    
    st.markdown(f"**Active Context:** {patient_record_dict['name']} ({patient_record_dict['uhid']}) | **Mobile:** {patient_record_dict['mobile']} | **Alerts:** `{patient_record_dict['alerts']}`")
    st.write("---")
    
    v_col1, v_col2, v_col3, v_col4, v_col5 = st.columns(5)
    with v_col1:
        st.text_input("Blood Pressure", value="120/80")
    with v_col2:
        st.number_input("Pulse Rate", value=72)
    with v_col3:
        st.number_input("SpO2 (%)", value=98)
    with v_col4:
        st.text_input("Body Temp", value="98.6 F")
    with v_col5:
        st.number_input("Respiratory Rate", value=16)
        
    c_notes = st.text_area("Chief Presenting Complaint Notes")
    rx_notes = st.text_area("Digital Prescription Layout Formulation")
    
    if st.button("Commit Complete Encounter Entry to Archive", type="primary", use_container_width=True):
        st.success(f"Encounter record saved for patient: {target_uhid}")

# ==============================================================================
# MODULE 4: SURGICAL SUITE & OT
# ==============================================================================
elif "🔪 Surgical Suite & OT" in module_selection:
    st.subheader("Interventional Surgical Suite & Operating Theatre Console")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        p_sel = st.selectbox("Select Patient", [f"{p['uhid']} - {p['name']}" for p in st.session_state.patients])
        proc = st.text_input("Procedure Title", value="Laparoscopic Hernia Repair")
        surgeon = st.text_input("Lead Surgeon", value="Dr. Prateek")
    with s_col2:
        ot = st.selectbox("OT Chamber", ["OT-1 Major Theatre", "OT-2 Laparoscopy Suite", "OT-3 Emergency Bay"])
        sdate = st.date_input("Scheduled Date", datetime.date.today())
        
    if st.button("Authorize Operating Theatre Schedule Slot Allocation", type="primary", use_container_width=True):
        st.session_state.surgeries.append({
            "id": f"SURG-10{len(st.session_state.surgeries)+1}", "uhid": p_sel.split(" - ")[0],
            "patient": p_sel.split(" - ")[1], "procedure": proc, "surgeon": surgeon,
            "date": sdate, "status": "Scheduled", "ot": ot
        })
        st.success("OT slot scheduled successfully.")
        st.rerun()
        
    st.dataframe(pd.DataFrame(st.session_state.surgeries), use_container_width=True)

# ==============================================================================
# MODULE 5: BILLING & DUAL-DISPATCH
# ==============================================================================
elif "💳 Medical Billing Ledger" in module_selection:
    st.subheader("Central Clinical Financial Ledger & Patient Billing Portal")
    b_col1, b_col2 = st.columns([2, 3])
    with b_col1:
        p_bill = st.selectbox("Select Patient Profile", [f"{p['uhid']} - {p['name']}" for p in st.session_state.patients])
        c_fees = st.number_input("Consultation Fee (INR)", value=1000)
        s_pack = st.number_input("Surgical Package (INR)", value=55000)
        inv_c = st.number_input("Diagnostic Imaging (INR)", value=4500)
        total = c_fees + s_pack + inv_c
        st.metric("Total Balance", f"₹{total:,.2f}")
        p_bemail = st.text_input("Billing Email ID", placeholder="patient@domain.com")
        
        if st.button("Seal Financial Statement Invoice & Push System Dispatches", type="primary", use_container_width=True):
            t_uhid = p_bill.split(" - ")[0]
            t_name = p_bill.split(" - ")[1]
            target_pt = next((p for p in st.session_state.patients if p["uhid"] == t_uhid), None)
            new_inv = {"invoice": f"INV-2026-00{len(st.session_state.billing) + 1}", "uhid": t_uhid, "patient": t_name, "amount": float(total), "status": "Pending", "date": datetime.date.today()}
            
            with st.spinner("Processing invoice and dual-dispatching..."):
                st.session_state.billing.append(new_inv)
                status_flag, ret_msg = compile_and_dispatch(
                    f"Invoice_{new_inv['invoice']}",
                    pd.DataFrame([new_inv]),
                    target_email=p_bemail,
                    target_whatsapp=target_pt.get("mobile") if target_pt else None
                )
                if status_flag:
                    st.success(f"Invoice {new_inv['invoice']} generated & dispatched!")
                else:
                    st.warning(ret_msg)
            time.sleep(2)
            st.rerun()
            
    with b_col2:
        st.dataframe(pd.DataFrame(st.session_state.billing), use_container_width=True)

# ==============================================================================
# MODULE 6: PHARMACY & INVENTORY
# ==============================================================================
elif "📦 Medical Pharmacy & Inventory" in module_selection:
    st.subheader("Medical Stock Logistics Warehouse & Inventory Console")
    
    total_qty = sum([int(item.get("stock", 0)) for item in st.session_state.inventory])
    item_types = len(st.session_state.inventory)
    low_stock = sum([1 for item in st.session_state.inventory if int(item.get("stock", 0)) <= int(item.get("min_level", 0))])
    
    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        st.metric("Total Unique Item Types", f"{item_types} Categories")
    with ic2:
        st.metric("Total Physical Stock Count", f"{total_qty} Units")
    with ic3:
        st.metric("Items Requiring Re-Order", f"{low_stock} Low Stock", delta=-low_stock if low_stock > 0 else 0)
        
    st.write("---")
    
    i_col1, i_col2 = st.columns([3, 7])
    with i_col1:
        st.markdown("#### Direct Inventory Actions")
        inv_mode = st.radio("Select Action", ["➕ Add / Restock Item", "✏️ Adjust Existing Stock", "❌ Remove Item Row"], horizontal=True)
        
        if inv_mode == "➕ Add / Restock Item":
            i_name = st.text_input("Supply Item Name", placeholder="e.g. Surgical Blades #11")
            i_type = st.selectbox("Category Group", ["Consumables", "Sutures", "Implants", "Equipments", "Medicines"])
            i_qty = st.number_input("Units to Add", min_value=1, value=25, step=5)
            i_min = st.number_input("Minimum Threshold Level", min_value=1, value=10, step=1)
            
            if st.button("Commit to Inventory Manifest", type="primary", use_container_width=True):
                if i_name.strip():
                    existing = next((item for item in st.session_state.inventory if item["item"].lower() == i_name.strip().lower()), None)
                    if existing:
                        existing["stock"] = int(existing["stock"]) + int(i_qty)
                        existing["min_level"] = int(i_min)
                        st.success(f"Restocked {i_name}! New total stock: {existing['stock']}")
                    else:
                        st.session_state.inventory.append({
                            "item": i_name.strip(),
                            "type": i_type,
                            "stock": int(i_qty),
                            "min_level": int(i_min)
                        })
                        st.success(f"Added {i_name} with {i_qty} units to manifest!")
                    
                    compile_and_dispatch("Inventory_Update", pd.DataFrame(st.session_state.inventory))
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Please enter a valid item name.")
                    
        elif inv_mode == "✏️ Adjust Existing Stock":
            if st.session_state.inventory:
                target_item_name = st.selectbox("Select Item to Update", [i["item"] for i in st.session_state.inventory])
                current_item = next(i for i in st.session_state.inventory if i["item"] == target_item_name)
                
                new_stock_val = st.number_input("Set Exact Stock Count", min_value=0, value=int(current_item["stock"]), step=1)
                new_min_val = st.number_input("Set Minimum Alert Threshold", min_value=0, value=int(current_item["min_level"]), step=1)
                
                if st.button("Apply Stock Adjustment", type="primary", use_container_width=True):
                    current_item["stock"] = int(new_stock_val)
                    current_item["min_level"] = int(new_min_val)
                    compile_and_dispatch("Inventory_Update", pd.DataFrame(st.session_state.inventory))
                    st.success(f"Updated {target_item_name} stock to {new_stock_val}!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.info("Inventory is empty.")
                
        elif inv_mode == "❌ Remove Item Row":
            if st.session_state.inventory:
                target_del = st.selectbox("Select Item to Delete", [i["item"] for i in st.session_state.inventory])
                if st.button("Delete Item from Manifest", type="primary", use_container_width=True):
                    st.session_state.inventory = [i for i in st.session_state.inventory if i["item"] != target_del]
                    compile_and_dispatch("Inventory_Update", pd.DataFrame(st.session_state.inventory))
                    st.success(f"Removed {target_del} from database!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.info("Inventory is empty.")

    with i_col2:
        st.markdown("#### Live Pharmacy & Clinical Stock Manifest (Interactive Editor)")
        if st.session_state.inventory:
            df_inv = pd.DataFrame(st.session_state.inventory)
            edited_df = st.data_editor(
                df_inv,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "item": st.column_config.TextColumn("Item Description", required=True),
                    "type": st.column_config.SelectboxColumn("Category", options=["Consumables", "Sutures", "Implants", "Equipments", "Medicines"], required=True),
                    "stock": st.column_config.NumberColumn("Current Units in Stock", min_value=0, step=1, required=True),
                    "min_level": st.column_config.NumberColumn("Alert Limit", min_value=0, step=1, required=True),
                },
                key="inventory_table_editor"
            )
            
            if not df_inv.equals(edited_df):
                st.session_state.inventory = edited_df.to_dict(orient="records")
                compile_and_dispatch("Inventory_Update", pd.DataFrame(st.session_state.inventory))
                st.toast("Inventory modifications synced to database & email dispatch!", icon="✅")
                time.sleep(1)
                st.rerun()
        else:
            st.info("No items found in active inventory.")

# ==============================================================================
# MODULE 7: CONSOLIDATED SYSTEM REPORTS
# ==============================================================================
elif "📊 Consolidated System Reports" in module_selection:
    st.subheader("Operational Business Intelligence Suite")
    r_type = st.radio("Select Report Scope", ["Daily Revenue Ledger", "Surgical Throughput Efficiency Report", "Pharmacy Inventory Manifest"], horizontal=True)
    
    if "Revenue" in r_type:
        r_df = pd.DataFrame(st.session_state.billing)
    elif "Surgical" in r_type:
        r_df = pd.DataFrame(st.session_state.surgeries)
    else:
        r_df = pd.DataFrame(st.session_state.inventory)
        
    st.dataframe(r_df, use_container_width=True)
    
    if st.button("Generate & Dispatch Report via Email + WhatsApp", type="primary", use_container_width=True):
        with st.spinner("Compiling and dispatching..."):
            status_flag, ret_msg = compile_and_dispatch(r_type.replace(" ", "_"), r_df)
            if status_flag:
                st.success("Report successfully dispatched via Email and WhatsApp!")
            else:
                st.warning(ret_msg)