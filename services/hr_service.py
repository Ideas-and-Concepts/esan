"""
HR Service
Employee management
"""

from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Employee

def get_all_employees():
    db = SessionLocal()
    try:
        return db.query(Employee).order_by(Employee.full_name).all()
    finally:
        db.close()

def create_employee(employee_code, full_name, department=None, position=None,
                    phone=None, email=None, hire_date=None, salary=None):
    db = SessionLocal()
    try:
        emp = Employee(
            employee_code=employee_code,
            full_name=full_name,
            department=department,
            position=position,
            phone=phone,
            email=email,
            hire_date=hire_date,
            salary=salary,
            status="Active",
            created_at=datetime.utcnow()
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
        return emp
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
