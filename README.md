
# Secure Trade AI

An AI-powered Customs Compliance and Invoice Risk Analysis System built using Python and Django.

## About the Project

Secure Trade AI helps analyze import-export invoices using Artificial Intelligence. It extracts invoice information, identifies potential anomalies, assesses customs duties and provides risk analysis to support customs compliance review.

## Features

- User Registration and Login
- AI-powered Invoice Data Extraction using Google Gemini
- Invoice Anomaly Detection
- HS Code Validation
- Customs Duty and Tax Assessment
- Invoice Risk Analysis and Visualization
- Invoice History with Search and Date Filters
- Invoice Status Management
- PDF Clearance Certificate Generation
- User Account and Profile Management

## Technologies Used

- Python
- Django
- HTML
- CSS
- JavaScript
- SQLite
- Google Gemini API
- Matplotlib
- Pillow
- ReportLab

## Installation

1. Clone the repository:

   git clone YOUR_REPOSITORY_URL

2. Open the project folder:

   cd trade_pro

3. Create a virtual environment:

   python -m venv venv

4. Activate the virtual environment:

   Windows:

   venv\Scripts\activate

5. Install dependencies:

   pip install -r requirements.txt

6. Create a `.env` file in the project root:

   DJANGO_SECRET_KEY=your_secret_key
   GEMINI_API_KEY=your_gemini_api_key

7. Run migrations:

   python manage.py migrate

8. Start the development server:

   python manage.py runserver

## Environment Variables

The project requires:

- DJANGO_SECRET_KEY
- GEMINI_API_KEY

Never upload your actual secret keys to GitHub.

## Project Status

Under Development.

## Author

Developed as an AI and Machine Learning focused academic project.

