# VendorBridge – Procurement & Vendor Management ERP

A production-style Django ERP for procurement operations: vendor management, RFQs, quotations, approvals, purchase orders, invoices, analytics, and role-based access control.

## Tech Stack

- **Frontend:** HTML5, CSS3, Bootstrap 5, Vanilla JavaScript, Chart.js
- **Backend:** Python 3, Django 5+
- **Database:** SQLite
- **PDF:** ReportLab

## Project Structure

```
vendorbridge/
├── config/              # Project settings & URLs
├── accounts/            # Authentication, users, roles
├── vendors/             # Vendor CRUD
├── procurement/         # RFQ, Quotations, Approvals, PO, Invoices
├── core/                # Dashboard, Activity Logs, Reports
├── templates/           # Bootstrap UI templates
├── static/              # CSS & JS
├── media/               # Uploaded files
└── manage.py
```

## Setup Instructions

```bash
cd vendorbridge
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_roles
python manage.py seed_data
python manage.py runserver
```

Open **http://127.0.0.1:8000/** in your browser.

## Demo Login Credentials

| Role                | Username      | Password      |
|---------------------|---------------|---------------|
| Admin               | admin         | Admin@123     |
| Procurement Officer | procurement   | Procure@123   |
| Manager / Approver  | manager       | Manager@123   |
| Vendor              | vendor1       | Vendor@123    |

## User Roles

- **Admin** – Manage users, vendors, analytics, all modules
- **Procurement Officer** – RFQs, vendor assignment, quotation comparison, PO & invoice generation
- **Vendor** – View assigned RFQs, submit/edit quotations, view POs
- **Manager / Approver** – Approve/reject requests, monitor workflows

## Features

- Secure authentication with role-based redirects
- Vendor CRUD with search & filters
- RFQ lifecycle management with vendor assignment
- Quotation submission, comparison (lowest price / fastest delivery highlights)
- Approval workflow with timeline tracking
- Auto-generated Purchase Orders & Invoices
- PDF download, print view, and email delivery for invoices
- Activity logging and in-app notifications
- Reports & analytics with CSV export

## Django Commands

```bash
python manage.py migrate          # Apply migrations
python manage.py setup_roles      # Create groups & permissions
python manage.py seed_data        # Load demo data
python manage.py createsuperuser  # Create additional admin
python manage.py runserver        # Start dev server
```

## Email Configuration

By default, emails are printed to the console. For production, update `EMAIL_BACKEND` in `config/settings.py`.

## License

MIT
