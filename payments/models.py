from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

def save(self, *args, **kwargs):
    self.amount_paid = self.amount_paid or Decimal("0.00")
    self.amount_owed = self.amount_owed or Decimal("0.00")
    super().save(*args, **kwargs)


class PaymentItem(models.Model):
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_mandatory = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - ₦{self.amount}"

    class Meta:
        ordering = ['-created_at']


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('abandoned', 'Abandoned'),
    ]

    # 🔥 Link directly to CustomUser
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    payment_items = models.ManyToManyField(PaymentItem, related_name='transactions')
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    channel = models.CharField(max_length=50, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Paystack customer details
    customer_code = models.CharField(max_length=100, blank=True)
    customer_id = models.CharField(max_length=100, blank=True)

    # Payment metadata (use TextField to avoid JSON_VALID issues in SQLite)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.TextField(blank=True, default='{}')

    # Refund info
    refunded = models.BooleanField(default=False)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference} - {self.user.email} - ₦{self.amount}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reference']),
        ]


class PaymentReceipt(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=50, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='receipts/', blank=True, null=True)

    def __str__(self):
        return f"Receipt {self.receipt_number}"


class PaymentReceipt(models.Model):
    transaction = models.OneToOneField(
        'Transaction',
        on_delete=models.CASCADE,
        related_name='receipt'
    )
    pdf_file = models.FileField(upload_to='receipts/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt for {self.transaction.reference}"


class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.code

    def is_valid(self):
        """Check if the coupon is valid for use"""
        if not self.active:
            return False
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return False
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False
        return True

    def apply_discount(self, amount):
        """Apply discount to a given amount"""
        if self.discount_amount:
            return max(0, amount - self.discount_amount)
        elif self.discount_percent:
            return max(0, amount * (1 - self.discount_percent / 100))
        return amount
