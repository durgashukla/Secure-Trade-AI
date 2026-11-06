from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm
from .genai_service import extract_invoice_data
from .invoice_service import save_invoice
from .anomaly_services import check_invoice_anomalies
from .tariff_service import validate_and_calculate_tariff
from .risk_chart import create_risk_gauge
from django.contrib.auth import authenticate, login as auth_login
from .models import Invoice
from django.shortcuts import redirect, get_object_or_404
from .risk_chart import generate_risk_chart,generate_weekly_chart
from django.contrib.auth import logout as auth_logout
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .forms import ProfileUpdateForm
from django.db.models import Q
from datetime import timedelta


def register(request):
    form = UserCreationForm()

    if request.method=='POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')

    return render(request,'register.html',{'form':form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')

        else:
            return render(request, "login.html", {
                "error": "Invalid username or password"
            })

    return render(request, "login.html")

from django.utils import timezone
from .models import Invoice



@login_required
def dashboard(request):
    today = timezone.localdate()
    user_invoices = Invoice.objects.filter(user=request.user)

    today_invoices = user_invoices.filter(
        invoice_date=str(today)
    ).order_by('-id')[:5]

    clear_count = user_invoices.filter(
        invoice_date=str(today), status="clear"
    ).count()

    pending_count = user_invoices.filter(
        invoice_date=str(today), status="pending"
    ).count()

    on_hold_count = user_invoices.filter(
        invoice_date=str(today), status="on_hold"
    ).count()

    fraud_count = user_invoices.filter(
        invoice_date=str(today), status="fraud"
    ).count()

    chart_path = generate_risk_chart(
    clear_count,
    pending_count,
    on_hold_count,
    fraud_count,
    request.user.id)

    weekly_chart_path = generate_weekly_chart(request.user.id)

    context = {
        "today_invoices": today_invoices,
        "clear_count": clear_count,
        "pending_count": pending_count,
        "on_hold_count": on_hold_count,
        "fraud_count": fraud_count,
        "chart_path": chart_path,
        "weekly_chart_path": weekly_chart_path,
    }

    return render(request, "dashboard.html", context)


@login_required
def view_invoice(request):

    today = timezone.localdate()

    all_invoices = Invoice.objects.filter(
        user=request.user
    ).order_by('-id')

    # Date Filter
    date_filter = request.GET.get('date', 'all')

    invoices = all_invoices

    if date_filter == 'today':

        invoices = invoices.filter(
            invoice_date=today.isoformat()
        )

    elif date_filter == '7days':

        start_date = today - timedelta(days=6)

        invoices = invoices.filter(
            invoice_date__gte=start_date.isoformat(),
            invoice_date__lte=today.isoformat()
        )

    elif date_filter == '30days':

        start_date = today - timedelta(days=29)

        invoices = invoices.filter(
            invoice_date__gte=start_date.isoformat(),
            invoice_date__lte=today.isoformat()
        )

    # Search Filter
    query = request.GET.get('q', '').strip()

    if query:

        invoices = invoices.filter(
            Q(invoice_number__icontains=query) |
            Q(seller_name__icontains=query) |
            Q(buyer_name__icontains=query)
        )

    context = {

        'view_invoice': invoices,

        'search_query': query,

        'date_filter': date_filter,

        'total_invoices': all_invoices.count(),

        'cleared_count': all_invoices.filter(
            status="clear"
        ).count(),

        'pending_count': all_invoices.filter(
            status="pending"
        ).count(),

        'on_hold_count': all_invoices.filter(
            status="on_hold"
        ).count(),

        'fraud_count': all_invoices.filter(
            status="fraud"
        ).count(),

    }

    return render(request, "view_invoice.html", context)

@login_required
def upload_invoice(request):

    if request.method == 'POST':

        invoice_file = request.FILES.get('invoice')

        if not invoice_file:
            return render(request, 'upload.html', {
                'error': 'Please select a file.'
            })

        file_name = invoice_file.name.lower()

        try:

            if file_name.endswith('.json'):

                raw_data = invoice_file.read().decode('utf-8-sig')
                result = json.loads(raw_data)

                if not isinstance(result, dict):
                    raise ValueError("Invalid JSON structure.")

            elif file_name.endswith(('.pdf', '.png', '.jpg', '.jpeg', '.webp')):

                result = extract_invoice_data(invoice_file)

                if not isinstance(result, dict):
                    raise ValueError("Invalid invoice data from Gemini.")

            else:
                raise ValueError("Unsupported file format.")

            if not result.get('invoice_number'):
                raise ValueError("Invoice number is missing.")

            if not isinstance(result.get('items'), list):
                raise ValueError("Invoice items are missing or invalid.")

            # Save invoice for the logged-in user
            saved_invoice = save_invoice(result, request.user)

            # Store invoice ID for testing page
            request.session['current_invoice_id'] = saved_invoice.id

            return redirect('testing_view')

        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:

            return render(request, 'upload.html', {
                'error': str(e)
            })

        except Exception as e:

            print("Upload Error:", e)

            return render(request, 'upload.html', {
                'error': 'Invoice processing failed.'
            })

    return render(request, 'upload.html')


import json
from pathlib import Path

from django.conf import settings
from .risk_service import calculate_risk



@login_required
def testing_view(request):

    invoice_id = request.session.get('current_invoice_id')

    if not invoice_id:
        return redirect('upload')

    saved_invoice = get_object_or_404(
        Invoice,
        id=invoice_id,
        user=request.user
    )

    # Prepare invoice data from database
    data = {
        "invoice_number": saved_invoice.invoice_number,
        "invoice_date": saved_invoice.invoice_date,
        "seller_name": saved_invoice.seller_name,
        "buyer_name": saved_invoice.buyer_name,
        "currency": saved_invoice.currency,
        "total_amount": saved_invoice.total_amount,
        "origin_country": saved_invoice.origin_country,
        "destination_country": saved_invoice.destination_country,
        "items": [
            {
                "item_name": item.item_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "hs_code": item.hs_code,
            }
            for item in saved_invoice.items.all()
        ]
    }

    # Anomaly checks
    anomilies = check_invoice_anomalies(saved_invoice)

    # Tariff calculation
    tariff_result = validate_and_calculate_tariff(data)

    total_customs_duty = sum(
        item.get("total_duty", 0)
        for item in tariff_result
        if item.get("tariff_found")
    )

    # Risk calculation
    risk_report = calculate_risk(
        anomilies,
        tariff_result
    )

    chart_path = create_risk_gauge(
    risk_report["risk_score"],
    risk_report["risk_level"],
    request.user.id,
    saved_invoice.id)

    return render(request, "testing.html", {
        "data": data,
        "anomilies": anomilies,
        "tariff_result": tariff_result,
        "risk_report": risk_report,
        "chart_path": chart_path,
        "saved_invoice": saved_invoice,
        "total_customs_duty": total_customs_duty,
    })


@login_required
def update_invoice_status(request, invoice_id):

    if request.method == "POST":

        invoice = get_object_or_404(
            Invoice,
            id=invoice_id,
            user=request.user
        )

        new_status = request.POST.get("status")

        allowed_statuses = ["clear", "pending", "on_hold", "fraud"]

        if new_status in allowed_statuses:

            invoice.status = new_status

            if new_status == "clear":
                if not invoice.clearance_date:
                    invoice.clearance_date = timezone.now()
            else:
                invoice.clearance_date = None

            invoice.save()

    return redirect("invoice_detail", invoice_id=invoice_id)


@login_required
def invoice_list(request, status):

    allowed_statuses = ["clear", "pending", "on_hold", "fraud"]

    if status not in allowed_statuses:
        return redirect("dashboard")

    today = timezone.localdate()

    invoices = Invoice.objects.filter(
        user=request.user,
        invoice_date=str(today),
        status=status
    ).order_by("-id")

    return render(request, "invoice_list.html", {
        "invoices": invoices,
        "status": status,
    })


@login_required
def invoice_detail(request, invoice_id):

    invoice = get_object_or_404(
        Invoice,
        id=invoice_id,
        user=request.user
    )

    # Database se invoice items lena
    items = invoice.items.all()

    # Invoice data prepare karna
    data = {
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date,
        "seller_name": invoice.seller_name,
        "buyer_name": invoice.buyer_name,
        "currency": invoice.currency,
        "total_amount": invoice.total_amount,
        "origin_country": invoice.origin_country or "",
        "destination_country": invoice.destination_country or "",
        "items": [
            {
                "item_name": item.item_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "hs_code": item.hs_code,
            }
            for item in items
        ],
    }

    # Anomaly checking
    anomilies = check_invoice_anomalies(invoice)

    # Customs duty calculation
    tariff_result = validate_and_calculate_tariff(data)

    # Total customs duty calculate karna
    total_customs_duty = sum(
        item.get("total_duty", 0)
        for item in tariff_result
        if item.get("tariff_found")
    )

    # Risk calculation
    risk_report = calculate_risk(
        anomilies,
        tariff_result
    )

    chart_path = create_risk_gauge(
    risk_report["risk_score"],
    risk_report["risk_level"],
    request.user.id,
    invoice.id
)

    return render(request, "testing.html", {
        "data": data,
        "anomilies": anomilies,
        "tariff_result": tariff_result,
        "risk_report": risk_report,
        "chart_path": chart_path,
        "saved_invoice": invoice,
        "total_customs_duty": total_customs_duty,
    })


@login_required
def search_invoice(request):

    query = request.GET.get('invoice_number', '').strip()

    invoices = []

    if query:
        invoices = Invoice.objects.filter(
            user=request.user,
            invoice_number__icontains=query
        ).order_by('-id')

    return render(request, 'search_results.html', {
        'invoices': invoices,
        'query': query
    })

from django.http import HttpResponse
from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from xml.sax.saxutils import escape

@login_required
def download_clearance_certificate(request, invoice_id):

    invoice = get_object_or_404(
        Invoice,
        id=invoice_id,
        user=request.user
    )
    

    # Only cleared invoices can download certificate
    if invoice.status != "clear" or not invoice.clearance_date:
        return redirect("invoice_detail", invoice_id=invoice_id)

    buffer = BytesIO()

    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25 * mm,
        leftMargin=25 * mm,
        topMargin=25 * mm,
        bottomMargin=25 * mm
    )

    styles = getSampleStyleSheet()

    story = []

    title_style = ParagraphStyle(
        "CertificateTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#17365D"),
        alignment=TA_CENTER,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.HexColor("#64748B")
    )

    # Header
    story.append(Paragraph("SECURE TRADE AI", title_style))

    story.append(
        Paragraph("TRADE COMPLIANCE & CLEARANCE CERTIFICATE", subtitle_style)
    )

    story.append(Spacer(1, 25))

    story.append(
        Paragraph(
            "CERTIFICATE OF SUCCESSFUL CLEARANCE",
            ParagraphStyle(
                "Heading",
                parent=styles["Heading2"],
                alignment=TA_CENTER,
                textColor=colors.HexColor("#15803D"),
                fontSize=15
            )
        )
    )

    story.append(Spacer(1, 20))

    # Invoice details
    invoice_data = [
        ["Invoice Number", str(invoice.invoice_number or "N/A")],
        ["Seller Name", str(invoice.seller_name or "N/A")],
        ["Buyer Name", str(invoice.buyer_name or "N/A")],
        ["Country of Origin", str(invoice.origin_country or "N/A")],
        ["Invoice Date", str(invoice.invoice_date or "N/A")],
        [
            "Total Invoice Value",
            f"{invoice.currency or ''} {invoice.total_amount or 'N/A'}"
        ],
        ["Clearance Status", "SUCCESSFULLY CLEARED"],
        [
            "Officer Clearance Date",
            timezone.localtime(invoice.clearance_date).strftime(
                "%d-%m-%Y %I:%M %p"
            )
        ],
    ]

    table = Table(
        [
            [Paragraph(escape(row[0]), styles["Normal"]),
             Paragraph(escape(row[1]), styles["Normal"])]
            for row in invoice_data
        ],
        colWidths=[65 * mm, 95 * mm],
        rowHeights=16 * mm
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EFF4FA")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#263445")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6DEE8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 6), (-1, 6), colors.HexColor("#DCFCE7")),
        ("TEXTCOLOR", (1, 6), (1, 6), colors.HexColor("#15803D")),
    ]))

    story.append(table)

    story.append(Spacer(1, 35))

    story.append(
        Paragraph(
            "This document confirms that the above invoice has been "
            "marked as successfully cleared in Secure Trade AI.",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 35))

    story.append(
        Paragraph(
            "Authorized Officer",
            ParagraphStyle(
                "Officer",
                parent=styles["Normal"],
                alignment=TA_CENTER,
                fontSize=11
            )
        )
    )

    
    if request.user.is_authenticated:
        officer_name = (
            request.user.get_full_name().strip()
            or request.user.username
        )
    else:
        officer_name = "Customs Officer"

    story.append(
        Paragraph(
            escape(officer_name),
            ParagraphStyle(
                "OfficerName",
                parent=styles["Normal"],
                alignment=TA_CENTER,
                fontSize=10
            )
        )
    )

    story.append(Spacer(1, 30))

    story.append(
        Paragraph(
            "Generated by Secure Trade AI",
            ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                alignment=TA_CENTER,
                textColor=colors.grey,
                fontSize=9
            )
        )
    )

    pdf.build(story)

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="Clearance_Certificate_{invoice.id}.pdf"'
    )

    return response

def logout_view(request):
    if request.method == "POST":
        auth_logout(request)
        return redirect('login')

    return redirect('dashboard')


@login_required
def account_view(request):

    user = request.user

    invoices = Invoice.objects.filter(user=user)

    total_invoices = invoices.count()

    cleared_invoices = invoices.filter(
        status="clear"
    ).count()

    pending_invoices = invoices.filter(
        status="pending"
    ).count()

    context = {
        "user": user,
        "total_invoices": total_invoices,
        "cleared_invoices": cleared_invoices,
        "pending_invoices": pending_invoices,
    }

    return render(request, "account.html", context)


@login_required
def edit_profile(request):

    if request.method == "POST":

        form = ProfileUpdateForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Profile updated successfully!"
            )
            return redirect("account")

    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, "edit_profile.html", {
        "form": form
    })


@login_required
def change_password(request):

    if request.method == "POST":

        form = PasswordChangeForm(
            user=request.user,
            data=request.POST
        )

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(
                request,
                user
            )

            messages.success(
                request,
                "Password changed successfully!"
            )

            return redirect("account")

    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, "change_password.html", {
        "form": form
    })