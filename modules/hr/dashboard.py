"""
HR Dashboard – uses hr_service
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
                "Status": e.status
            } for e in employees]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No employees.")
    with tab2:
        with st.form("add_employee"):
            code = st.text_input("Employee Code *")
            name = st.text_input("Full Name *")
            dept = st.selectbox("Department", ["Milling", "Packaging", "Sales", "Finance", "Logistics", "HR", "Maintenance"])
            position = st.text_input("Position")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            hire = st.date_input("Hire Date", datetime.now().date())
            salary = st.number_input("Salary", min_value=0.0)
            if st.form_submit_button("Save"):
                if code and name:
                    create_employee(code, name, dept, position, phone, email, hire, salary)
                    st.success("Employee added")
                    st.rerun()
