
from django.db import models
from django.conf import settings


class Invoice(models.Model):

    # Multi-user support
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoices",
        null=True,
        blank=True
    )

    invoice_number = models.CharField(max_length=100, null=True, blank=True)
    invoice_date = models.CharField(max_length=100, null=True, blank=True)
    seller_name = models.CharField(max_length=200, null=True, blank=True)
    buyer_name = models.CharField(max_length=200, null=True, blank=True)
    currency = models.CharField(max_length=20, null=True, blank=True)
    total_amount = models.CharField(max_length=100, null=True, blank=True)
    origin_country = models.CharField(max_length=20, null=True, blank=True)
    destination_country = models.CharField(max_length=20, null=True, blank=True)

    STATUS_CHOICES = [
        ('clear', 'Clear'),
        ('pending', 'Pending'),
        ('on_hold', 'On Hold'),
        ('fraud', 'Fraud'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    clearance_date = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.invoice_number or "Invoice"


class InvoiceItem(models.Model):

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items"
    )

    item_name = models.CharField(max_length=200)
    quantity = models.CharField(max_length=50, null=True, blank=True)
    unit_price = models.CharField(max_length=100, null=True, blank=True)
    total_price = models.CharField(max_length=100, null=True, blank=True)
    hs_code = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.item_name


class ReferencePrice(models.Model):

    item_name = models.CharField(max_length=200)
    unit = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name}-{self.price}/{self.unit}"


class TariffRate(models.Model):

    hs_code = models.CharField(max_length=8)
    product_name = models.CharField(max_length=200)

    origin_country = models.CharField(max_length=100)
    destination_country = models.CharField(max_length=100)

    bcd_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    sws_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    igst_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    other_duty_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )

    def __str__(self):
        return f"{self.hs_code} - {self.product_name}"
