Esan ERP

Enterprise Milling & Packaging Management System

Company: Nile Harvest Foods Ltd.
Version: 1.0.0 Alpha
Status: Alpha / Active Development

---

Overview

Esan ERP is an enterprise management platform designed for Nile Harvest Foods Ltd. to manage the operational, commercial, warehouse, production, and financial activities of an agricultural milling and packaging business.

The system is being developed to support the complete operational chain:

Procurement
    ↓
Warehouse
    ↓
Milling
    ↓
Packaging
    ↓
Sales & Distribution
    ↓
Delivery
    ↓
Invoicing
    ↓
Payments
    ↓
Finance & Accounting
    ↓
Reporting

The application is designed with a modular architecture so individual business functions can be developed, tested, and integrated independently.

---

Core Modules

Esan ERP is organized around the following major business areas:

Overview

Provides the operational dashboard and high-level business status.

Procurement

Manages:

- Suppliers
- Purchase Orders
- Purchases
- Procurement records
- Supplier information

Warehouse

Manages:

- Products
- Stock quantities
- Stock movements
- Inventory availability
- Stock reservations

Milling

Manages:

- Milling batches
- Raw-material inputs
- Production outputs
- Waste
- Production status

Packaging

Manages:

- Packaging batches
- Finished products
- Package sizes
- Number of packages
- Packaging production

Sales & Distribution

Manages:

- Customers
- Quotations
- Sales Orders
- Stock reservation
- Dispatch
- Deliveries
- Invoices
- Payments

Finance

Provides the foundation for:

- Accounts
- Journal Entries
- Journal Entry Lines
- Financial transactions
- Accounting integration

Reports

Provides business reporting and operational analysis.

---

Sales Workflow

The intended commercial workflow is:

Customer
   ↓
Quotation
   ↓
Sales Order
   ↓
Stock Reservation
   ↓
Dispatch
   ↓
Delivery
   ↓
Invoice
   ↓
Payment
   ↓
Accounting

The quotation and Sales Order workflow is designed to preserve traceability between the original customer quotation and the resulting order.

---

Quotation Management

The quotation service provides functionality for:

- Creating quotations
- Generating quotation numbers
- Updating quotations
- Adding quotation items
- Updating quotation items
- Removing quotation items
- Calculating quotation totals
- Cancelling quotations
- Converting quotations into Sales Orders

Quotation numbers use the format:

Q-00001
Q-00002
Q-00003

Quotation line totals are calculated from:

quantity × unit_price

The quotation header stores the resulting value in:

Quotation.total_amount

while each individual line stores its value in:

QuotationItem.total

---

Quotation → Sales Order Conversion

A quotation can be converted into a Sales Order once it contains at least one quotation item.

The conversion maintains the relationship:

Quotation
    │
    └── SalesOrder
            │
            ├── SalesOrderItem
            ├── SalesOrderItem
            └── SalesOrderItem

For every:

QuotationItem

exactly one:

SalesOrderItem

is created.

The following information is transferred:

- Product
- Product name
- Quantity
- Unit price
- Line total

Sales Orders use the format:

SO-00001
SO-00002
SO-00003

After successful conversion, the quotation status becomes:

Converted

A quotation cannot be converted twice.

The database is intended to enforce one Sales Order per quotation through a unique constraint on:

sales_orders.quotation_id

Constraint name:

uq_sales_orders_quotation_id

---

Stock Reservation

Stock reservation is performed against Sales Order items.

The intended inventory calculation is:

Available Stock
=
Product.quantity
-
Reservations committed to other SalesOrderItems

Reservation operations are designed to:

1. Lock the relevant Product row.
2. Calculate available stock.
3. Validate requested quantity.
4. Update the Sales Order item's reserved quantity.
5. Commit the reservation atomically.

If any Sales Order line does not have sufficient available stock, the complete reservation transaction is rolled back.

This prevents a partially-reserved Sales Order.

---

Database Models

The SQLAlchemy data model includes entities for:

Users
Customers
Suppliers
Products

Purchase Orders
Purchase Order Items
Purchases
Purchase Items

Stock Movements
Warehouses

Milling Batches
Packaging Batches

Quotations
Quotation Items

Sales Orders
Sales Order Items

Deliveries
Delivery Items

Invoices
Invoice Items

Payments

Accounts
Journal Entries
Journal Entry Lines

The application uses SQLAlchemy ORM models with relationships between the major business entities.

---

Technology Stack

Esan ERP currently uses:

- Python
- Streamlit
- SQLAlchemy
- SQLite for development/testing where configured
- PostgreSQL for production deployments where configured
- Pytest
- FastAPI components for API integration where applicable

---

Project Structure

The project is organized approximately as follows:

esan/
│
├── streamlit_app.py
│
├── models.py
├── database.py
│
├── services/
│   └── quotation_service.py
│
├── modules/
│   └── sales/
│       └── quotations.py
│
├── tests/
│   └── test_quotation_conversion.py
│
├── scripts/
│   └── database migration and diagnostic scripts
│
├── assets/
│
├── requirements.txt
│
└── README.md

The project structure may evolve as additional ERP modules are implemented.

---

Installation

1. Clone Repository

git clone https://github.com/Ideas-and-Concepts/esan.git

Change into the project directory:

cd esan

---

2. Create Virtual Environment

Windows

python -m venv .venv
.venv\Scripts\activate

Linux / macOS

python3 -m venv .venv
source .venv/bin/activate

---

3. Install Dependencies

pip install -r requirements.txt

---

Database Configuration

The database configuration is managed through the project's database configuration.

For development, SQLite may be used.

For production, PostgreSQL is recommended.

Before applying database migrations to an existing production database:

1. Back up the database.
2. Scan for duplicate records.
3. Resolve existing data conflicts.
4. Apply the migration.
5. Verify the resulting constraints.

---

Database Migration

Database migrations should be treated as controlled production operations.

For example, before adding the unique quotation relationship:

sales_orders.quotation_id

existing duplicates must first be identified.

The migration should not automatically delete or modify business records.

A duplicate quotation relationship should be reviewed and resolved according to the business record that is authoritative.

The unique database object is:

uq_sales_orders_quotation_id

After migration, the database should enforce:

One quotation → maximum one Sales Order

Multiple Sales Orders may still have:

quotation_id = NULL

because unquoted Sales Orders are permitted by the model.

---

Testing

The project uses pytest for regression testing.

Run the complete test suite:

pytest -q

Run quotation conversion tests:

pytest -q tests/test_quotation_conversion.py

The quotation tests verify important business invariants including:

- Quotation totals
- Quotation item totals
- Sales Order creation
- Sales Order item creation
- One SalesOrderItem per QuotationItem
- Matching product information
- Matching quantities
- Matching unit prices
- Matching line totals
- Quotation status becoming "Converted"
- Prevention of duplicate quotation conversion

---

Import Diagnostics

Before launching Streamlit, quotation services can be checked independently.

Verify the quotation service:

python -c "from services.quotation_service import calculate_quotation_total, convert_quotation_to_sales_order; print('quotation_service: OK')"

Verify the sales quotation module:

python -c "from modules.sales.quotations import *; print('modules.sales.quotations: OK')"

These checks make it possible to identify Python import problems before they become Streamlit module-loading errors.

---

Running the Application

Start Streamlit with:

streamlit run streamlit_app.py

The application should open in the browser at the Streamlit development URL.

---

Development Principles

Esan ERP follows several important development principles.

Transactional Integrity

Business operations that modify multiple related records should be performed atomically.

For example:

Sales Order
    +
Sales Order Items
    +
Stock Reservation

should not leave partially completed records when an operation fails.

---

Database-Level Integrity

Important business rules should not rely exclusively on application code.

Where appropriate, constraints should also be enforced by the database.

Examples include:

Unique quotation numbers
Unique Sales Order numbers
One Sales Order per quotation
Foreign-key relationships

---

Regression Testing

Business-critical workflows should have automated regression tests before they are expanded.

Quotation conversion is one such workflow.

---

Modular Architecture

Business functionality should remain separated into services and modules rather than placing all business logic inside "streamlit_app.py".

For example:

UI
 ↓
Module
 ↓
Service
 ↓
SQLAlchemy Model
 ↓
Database

This makes the ERP easier to test, maintain, and eventually expose through APIs or other interfaces.

---

Error Handling

Services should:

- Validate input
- Validate referenced records
- Roll back failed database transactions
- Preserve database consistency
- Raise meaningful exceptions
- Handle database integrity errors where appropriate

In particular, duplicate quotation conversion should be protected by both:

Application-level validation

and:

Database-level uniqueness

This provides protection against both normal user mistakes and concurrent transactions.

---

Production Roadmap

The planned development sequence is:

1. Sales Orders
2. Stock Reservation
3. Delivery Notes
4. Invoice Creation
5. Payment Processing
6. Accounting Integration
7. Warehouse Integration
8. Sales → Inventory → Finance Integration
9. Procurement Integration
10. Milling Integration
11. Packaging Integration
12. Reporting & Analytics
13. Production Deployment

---

Project Status

Current status: Alpha

The system is under active development.

Core ERP models and business workflows are being implemented incrementally, with emphasis on:

- Data integrity
- Transaction safety
- Automated testing
- Modular architecture
- Production readiness
- Traceability between commercial and inventory transactions

Features marked as planned or under development should not be considered production-ready until their corresponding services, UI workflows, database behavior, and automated tests have been completed.

---

Company

Nile Harvest Foods Ltd.

Esan ERP is being developed as the enterprise management platform for the company's milling, packaging, sales, distribution, inventory, and financial operations.

---

License

Copyright © Nile Harvest Foods Ltd.

All rights reserved unless otherwise specified by the project repository.