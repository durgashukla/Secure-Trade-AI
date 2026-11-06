def calculate_risk(anomalies, tariff_results):
    score = 0
    reasons = []
    manual_checking = []

    # Anomaly dictionary
    items = anomalies.get("items", {})

    # 1. Item Total Price Mismatch
    for item_name, checks in items.items():

        if checks.get("item_total_mismatch", False):
            score += 20

            reasons.append(
                f"Item calculation mismatch: {item_name} (+20)"
            )

            

    # 2. Invoice Grand Total Mismatch
    if anomalies.get("invoice_total_mismatch", False):
        score += 30

        reasons.append("Invoice total mismatch (+30)")



    # 3. Tariff / HS Code Not Found
    for result in tariff_results:
        item_name = result.get("item_name", "Unknown")

        if not result.get("tariff_found", False):
            score += 20

            reasons.append(
                f"Tariff/HS Code not found: {item_name} (+20)"
            )

            manual_checking.append({
                "item_name": item_name,
                "reason": "Tariff / HS Code record not found",
                "status": "Pending"
            })

    # 4. Product Name and HS Code Mismatch
    for result in tariff_results:
        item_name = result.get("item_name", "Unknown")

        if (
            result.get("tariff_found", False)
            and result.get("product_matches") is False
        ):
            score += 15

            reasons.append(
                f"Product name mismatch: {item_name} (+15)"
            )

            manual_checking.append({
                "item_name": item_name,
                "reason": "Product name and HS Code need verification",
                "status": "Pending"
            })

    # 5. Reference Price Check
    for item_name, checks in items.items():

        # Reference price unavailable
        if checks.get("reference_price") is None:
            manual_checking.append({
                "item_name": item_name,
                "reason": "Reference price not available",
                "status": "Pending"
            })

        # Reference price deviation
        percentage = checks.get("difference_percentage")

        if percentage is not None and percentage > 10:

            if percentage <= 20:
                points = 5
            elif percentage <= 40:
                points = 10
            else:
                points = 15

            score += points

            reasons.append(
                f"Reference price mismatch: {item_name} "
                f"({percentage:.2f}% deviation, +{points})"
            )

            manual_checking.append({
                "item_name": item_name,
                "reason": (
                    f"Reference price deviation is {percentage:.2f}%"
                ),
                "status": "Pending"
            })

        # Reference price mismatch, even if deviation is 10% or less
        elif checks.get("reference_price_mismatch", False):
            manual_checking.append({
                "item_name": item_name,
                "reason": "Actual price differs from reference price",
                "status": "Pending"
            })

    # Maximum score
    score = min(score, 100)

    # Risk level
    if score < 30:
        level = "Low"
    elif score < 60:
        level = "Medium"
    else:
        level = "High"

    return {
        "risk_score": score,
        "risk_level": level,
        "risk_reasons": reasons,
        "manual_checking": manual_checking,
    }