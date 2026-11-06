
from .models import Invoice, InvoiceItem


def save_invoice(data, user):

    invoice = Invoice.objects.create(
        user=user,
        invoice_number=data.get("invoice_number"),
        invoice_date=data.get("invoice_date"),
        seller_name=data.get("seller_name"),
        buyer_name=data.get("buyer_name"),
        currency=data.get("currency"),
        total_amount=data.get("total_amount"),
        origin_country=data.get("origin_country"),
        destination_country=data.get("destination_country"),
    )

    for item in data.get("items", []):
        InvoiceItem.objects.create(
            invoice=invoice,
            item_name=item.get("item_name"),
            quantity=item.get("quantity"),
            unit_price=item.get("unit_price"),
            total_price=item.get("total_price"),
            hs_code=item.get("hs_code"),
        )

    return invoice
