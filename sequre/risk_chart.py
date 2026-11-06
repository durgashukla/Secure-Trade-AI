
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from django.conf import settings
from datetime import timedelta
from django.utils import timezone

from .models import Invoice


def generate_risk_chart(clear, pending, on_hold, fraud, user_id):

    labels = ["Clear", "Pending", "On Hold", "Fraud"]
    values = [clear, pending, on_hold, fraud]

    colors = ["#0E60A7", "#F4B942", "#6B9014", "#E76F51"]

    total = sum(values)

    fig, ax = plt.subplots(figsize=(6, 5))

    if total > 0:
        ax.pie(
            values,
            colors=colors,
            startangle=90,
            autopct=lambda p: f"{p:.1f}%" if p > 0 else "",
            wedgeprops={"width": 0.4, "edgecolor": "white"},
            pctdistance=0.8
        )
    else:
        ax.pie(
            [1],
            colors=["lightgray"],
            wedgeprops={"width": 0.4, "edgecolor": "white"}
        )

    from matplotlib.patches import Patch

    legend_items = [
        Patch(facecolor=color, label=label)
        for color, label in zip(colors, labels)
    ]

    ax.legend(
        handles=legend_items,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=2
    )

    ax.set_title("Invoice Status")
    ax.axis("equal")

    chart_dir = os.path.join(
        settings.MEDIA_ROOT, "user_charts", str(user_id)
    )
    os.makedirs(chart_dir, exist_ok=True)

    chart_path = os.path.join(chart_dir, "risk_chart.png")

    fig.savefig(chart_path, bbox_inches="tight")
    plt.close(fig)

    return settings.MEDIA_URL + f"user_charts/{user_id}/risk_chart.png"


def create_risk_gauge(risk_score, risk_level, user_id, invoice_id):

    score = max(0, min(100, float(risk_score)))

    fig, ax = plt.subplots(figsize=(5, 5))

    ax.pie(
        [score, 100 - score],
        colors=["#D49414", "lightgray"],
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.3}
    )

    ax.text(
        0, 0,
        f"{score:.0f}/100\n{risk_level} Risk",
        ha="center",
        va="center",
        fontsize=14
    )

    ax.axis("equal")

    chart_dir = os.path.join(
        settings.MEDIA_ROOT,
        "user_charts",
        str(user_id)
    )

    os.makedirs(chart_dir, exist_ok=True)

    filename = f"risk_gauge_{invoice_id}.png"
    chart_path = os.path.join(chart_dir, filename)

    fig.savefig(chart_path, bbox_inches="tight")
    plt.close(fig)

    return (
        settings.MEDIA_URL
        + f"user_charts/{user_id}/{filename}"
    )


def generate_weekly_chart(user_id):

    today = timezone.localdate()
    start_date = today - timedelta(days=6)

    dates = []
    clear_counts = []
    fraud_counts = []

    for i in range(7):

        day = start_date + timedelta(days=i)

        clear_count = Invoice.objects.filter(
            user_id=user_id,
            invoice_date=str(day),
            status="clear"
        ).count()

        fraud_count = Invoice.objects.filter(
            user_id=user_id,
            invoice_date=str(day),
            status="fraud"
        ).count()

        dates.append(day.strftime("%d %b"))
        clear_counts.append(clear_count)
        fraud_counts.append(fraud_count)

    x = range(7)

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.bar(
        [i - 0.2 for i in x],
        clear_counts,
        width=0.4,
        color="#0E60A7",
        label="Clear"
    )

    ax.bar(
        [i + 0.2 for i in x],
        fraud_counts,
        width=0.4,
        color="#E76F51",
        label="Fraud"
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels(dates)

    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Invoices")
    ax.set_title("Clear vs Fraud - Last 7 Days")

    ax.legend()
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    chart_dir = os.path.join(
        settings.MEDIA_ROOT, "user_charts", str(user_id)
    )
    os.makedirs(chart_dir, exist_ok=True)

    chart_path = os.path.join(chart_dir, "weekly_chart.png")

    fig.savefig(chart_path, bbox_inches="tight")
    plt.close(fig)

    return settings.MEDIA_URL + f"user_charts/{user_id}/weekly_chart.png"
