
from google import genai
from PIL import Image
import json
import os

# Read Gemini API Key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env file")

client = genai.Client(api_key=GEMINI_API_KEY)


def extract_invoice_data(invoice_file):

    image = Image.open(invoice_file)

    prompt = """
Analyze this invoice image.

Extract only the useful invoice information.

Return ONLY valid JSON in this exact format:

{
    "invoice_number": "",
    "invoice_date": "",
    "seller_name": "",
    "buyer_name": "",
    "currency": "",
    "total_amount": "",
    "items": [
        {
            "item_name": "",
            "quantity": "",
            "unit_price": "",
            "total_price": ""
        }
    ]
}

Rules:
- Read the information directly from the invoice.
- Do not guess missing information.
- If a field is not available, use null.
- Return only JSON.
- Do not use ```json or markdown.
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=[image, prompt]
    )

    return json.loads(response.text)
