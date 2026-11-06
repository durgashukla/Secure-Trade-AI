from .models import TariffRate


def validate_and_calculate_tariff(invoice_data):
    results = []

    for item in invoice_data.get("items", []):
        item_name = item.get("item_name", "")
        hs_code = str(item.get("hs_code") or "").strip()
        quantity = float(item.get("quantity") or 0)
        unit_price = float(item.get("unit_price") or 0)

        # Invoice se country information
        origin = invoice_data.get("origin_country", "")
        destination = invoice_data.get("destination_country", "")

        # HS Code missing check
        if not hs_code:
            results.append({
                "item_name": item_name,
                "hs_code": "",
                "status": "HS Code missing",
                "tariff_found": False,
            })
            continue

        # HS Code aur countries ko database mein search karo
        tariff = TariffRate.objects.filter(
            hs_code=hs_code,
            origin_country__iexact=origin,
            destination_country__iexact=destination,
        ).first()

        # Record nahi mila
        if not tariff:
            results.append({
                "item_name": item_name,
                "hs_code": hs_code,
                "status": "HS Code / tariff record not found",
                "tariff_found": False,
            })
            continue

        # Product name ko database ke product se compare karo
        product_matches = (
            item_name.strip().casefold()
            == tariff.product_name.strip().casefold()
        )

        if product_matches:
            status = "HS Code record and product name match"
        else:
            status = "Product name mismatch - manual verification needed"

        # Declared item value
        assessable_value = quantity * unit_price

        # Demo tariff rates ko percentage maana gaya hai
        bcd = assessable_value * float(tariff.bcd_rate) / 100
        sws = assessable_value * float(tariff.sws_rate) / 100
        igst = assessable_value * float(tariff.igst_rate) / 100
        other_duty = (
            assessable_value * float(tariff.other_duty_rate) / 100
        )

        total_duty = bcd + sws + igst + other_duty

        results.append({
            "item_name": item_name,
            "hs_code": hs_code,
            "status": status,
            "tariff_found": True,
            "product_matches": product_matches,
            "assessable_value": round(assessable_value, 2),
            "bcd": round(bcd, 2),
            "sws": round(sws, 2),
            "igst": round(igst, 2),
            "other_duty": round(other_duty, 2),
            "total_duty": round(total_duty, 2),
        })

    return results