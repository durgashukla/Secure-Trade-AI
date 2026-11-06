from .models import InvoiceItem, ReferencePrice, Invoice


def check_item_anomaly(quantity, unit_price, total_price, reference_price):
    expected_total = float(quantity) * float(unit_price)
    actual_total = float(str(total_price).replace(",", ""))

    results = {}

    if abs(expected_total - actual_total) > 0.01:
        results["item_total_mismatch"] = True
    else:
        results["item_total_mismatch"] = False

    if reference_price is not None:
        actual_price = float(unit_price)
        reference = float(reference_price)

        difference = abs(actual_price - reference)

        results["reference_price"] = reference
        results["actual_price"] = actual_price
        results["difference"] = difference

        if reference != 0:
            percentage = (difference / reference) * 100
            results["difference_percentage"] = round(percentage, 2)
        else:
            results["difference_percentage"] = None

        results["reference_price_mismatch"] = (
            actual_price != reference
        )
    else:
        results["reference_price"] = None
        results["reference_price_mismatch"] = None

    return results


def check_invoice_anomalies(invoice):
    items = InvoiceItem.objects.filter(invoice=invoice)

    anomalies = {
        "items": {},
        "invoice_total_mismatch": False
    }

    calculated_total = 0.0

    for item in items:
        reference = ReferencePrice.objects.filter(
            item_name__iexact=item.item_name
        ).first()

        reference_price = reference.price if reference else None

        result = check_item_anomaly(
            item.quantity,
            item.unit_price,
            item.total_price,
            reference_price,
        )

        anomalies["items"][item.item_name] = result

        calculated_total += float(
            str(item.total_price).replace(",", "")
        )

    invoice_total = float(
        str(invoice.total_amount).replace(",", "")
    )

    if abs(calculated_total - invoice_total) > 0.01:
        anomalies["invoice_total_mismatch"] = True
    else:
        anomalies["invoice_total_mismatch"] = False

    return anomalies