"""
HR Dashboard
Esan ERP - Employee Management
"""

import streamlit as st
import pandas as pd
from services.hr_service import get_all_employees, create_employee
from datetime import datetime

def hr_dashboard():
    st.title("👥 HR & Employees")
    tab1, tab2 = st.tabs(["Employee List", "Add Employee"])

    with tab1:
        employees = get_all_employees()
        if employees:
            data = [{
                "Code": e.employee_code,
                "Name": e.full_name,
                "Department": e.department,
                "Position": e.position,
                "Phone": e.phone,
                "Email": e.email,
                "Hire Date": e.hire_date.strftime('%Y-%m-%d') if e.hire_date else "",
                "Status": e.status
            } for e in employees]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No employees found.")

    with tab2:
        st.subheader("➕ New Employee")
        with st.form("add_employee_form"):
            code = st.text_input("Employee Code *")
            full_name = st.text_input("Full Name *")
            dept = st.selectbox("Department", ["Milling", "Packaging", "Sales", "Finance", "Logistics", "HR", "Maintenance"])
            position = st.text_input("Position")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            hire = st.date_input("Hire Date", datetime.today())
            salary = st.number_input("Salary", min_value=0.0, step=100.0)
            if st.form_submit_button("Save Employee"):
                if not code or not full_name:
                    st.error("Code and Name are required.")
                else:
                    create_employee(code, full_name, dept, position, phone, email, hire, salary)
                    st.success("Employee added successfully.")
                    st.rerun()