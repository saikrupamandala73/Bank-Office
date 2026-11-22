#Bank Office – Smart Financial Management System

#Overview

Bank Office is a modern financial management platform designed to simplify everyday financial operations. It provides invoice and bill management, multi-currency support, and a multilingual interface in one place.

#Key Features

- Multi-Currency Support: Supports INR, USD, EUR, GBP, AED, and JPY.
- Currency Conversion: Exchange-rate integration for displaying financial amounts in different currencies.
- Multilingual Interface: Language options including English, Telugu, Hindi, Tamil, and Kannada.
- Dashboard: Centralized view of financial information and summaries.
- Invoice Management: Organize and track invoices.
- Bill Management: Manage and monitor bills.

#Technology Stack

- Frontend: React, Vite
- Backend: Python, FastAPI
- Database: SQLAlchemy
- Testing: API tests and frontend build

#Project Structure

Bank-Office/
├── Backend/
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   └── seed.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
└── README.md

Getting Started

#Backend

1. Open the Backend directory.
2. Install dependencies:

pip install -r requirements.txt

3. Start the FastAPI server:

uvicorn app.main:app --reload

#Frontend

1. Open the frontend directory.
2. Install dependencies:

npm install

3. Start the development server:

npm run dev

Project Goal

To make financial management more accessible through multilingual support, multi-currency functionality, and a simple interface for everyday invoice and bill management.
