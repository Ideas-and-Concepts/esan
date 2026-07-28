"""
HR Dashboard
Esan ERP - Employee Management
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import SessionLocal
from models import Employee

def get_db():
    return SessionLocal()

def hr_dashboard():
    st.title("👥 HR & Employees")
    tab1, tab2 = st.tabs(["Employee List", "Add Employee"])
    with tab1:
        employee_list()
    with tab2:
        add_employee()

def employee_list():
    db = get_db()
    try:
        employees = db.query(Employee).all()
        if employees:
            data = [{
                'Code': e.employee_code,
                'Name': e.full_name,
                'Department': e.department,
                'Position': e.position,
                'Phone': e.phone,
                'Email': e.email,
                'Hire Date': e.hire_date.strftime('%Y-%m-%d') if e.hire_date else '',
                'Status': e.status
            } for e in employees]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No employees found.")
    finally:
        db.close()

def add_employee():
    st.subheader("New Employee")
    with st.form("add_employee"):
        code = st.text_input("Employee Code*")
        name = st.text_input("Full Name*")
        dept = st.selectbox("Department", ["Milling", "Packaging", "Sales", "Finance", "Logistics", "HR", "Maintenance"])
        position = st.text_input("Position")
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        hire = st.date_input("Hire Date", datetime.now().date())
        salary = st.number_input("Salary", min_value=0.0)
        if st.form_submit_button("Save"):
            if not code or not name:
                st.error("Code and Name are required")
                return
            db = get_db()
            try:
                emp = Employee(
                    employee_code=code, full_name=name, department=dept,
                    position=position, phone=phone, email=email,
                    hire_date=hire, salary=salary, status="Active",
                    created_at=datetime.utcnow()
                )
                db.add(emp)
                db.commit()
                st.success("Employee added!")
                st.rerun()
            except Exception as e:
                db.rollback()
                st.error(f"Error: {e}")
            finally:
                db.close()