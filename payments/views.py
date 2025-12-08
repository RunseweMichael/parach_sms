import hashlib
# ✅ Safe monkey-patch for 'usedforsecurity' keyword issue
_real_md5 = hashlib.md5
def safe_md5(*args, **kwargs):
    kwargs.pop("usedforsecurity", None)
    return _real_md5(*args, **kwargs)
hashlib.md5 = safe_md5


from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from .utils_receipt import generate_receipt_pdf
from django.utils import timezone
from decimal import Decimal
from django.http import JsonResponse
import hmac
import hashlib
from students.models import CustomUser
from .models import PaymentItem, Transaction, PaymentReceipt, Coupon
from .serializers import PaymentItemSerializer, TransactionSerializer, UserSerializer, PaymentReceiptSerializer
from rest_framework import status
from django.conf import settings
from decimal import Decimal, InvalidOperation
import uuid, json, requests
from rest_framework import generics, permissions
from django.http import FileResponse, Http404
from .models import PaymentReceipt



PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
PAYSTACK_BASE_URL = 'https://api.paystack.co'


import json

def parse_metadata(metadata):
    """Ensure metadata is always a dict."""
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}
    elif not isinstance(metadata, dict):
        metadata = {}
    return metadata


# ==========================================================
# USERS (STUDENTS) VIEWSET
# ==========================================================
class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(id=self.request.user.id)

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        user = self.get_object()
        # ✅ Filter transactions by current course
        transactions = Transaction.objects.filter(user=user, course=user.course)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def payment_summary(self, request, pk=None):
        user = self.get_object()
        # ✅ Filter by current course
        transactions = Transaction.objects.filter(user=user, course=user.course)
        total_paid = transactions.filter(status='success').aggregate(total=Sum('amount'))['total'] or 0
        pending = transactions.filter(status='pending').count()
        failed = transactions.filter(status='failed').count()

        return Response({
            'total_paid': float(total_paid),
            'successful_payments': transactions.filter(status='success').count(),
            'pending_payments': pending,
            'failed_payments': failed,
            'total_transactions': transactions.count(),
        })


# ==========================================================
# PAYMENT ITEM VIEWSET
# ==========================================================
class PaymentItemViewSet(viewsets.ModelViewSet):
    queryset = PaymentItem.objects.all()
    serializer_class = PaymentItemSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = PaymentItem.objects.all()
        is_active = self.request.query_params.get('is_active', None)
        payment_type = self.request.query_params.get('payment_type', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if payment_type:
            queryset = queryset.filter(payment_type=payment_type)
        return queryset


# ==========================================================
# GET BALANCE ENDPOINT
# ==========================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_balance(request):
    user = request.user
    if not user.course:
        return Response({'error': 'User has no assigned course.'}, status=400)

    course_price = Decimal(str(user.course.price))
    
    # ✅ Compute total paid dynamically - ONLY for current course
    total_paid = Transaction.objects.filter(
        user=user, 
        status='success',
        course=user.course  # ✅ Filter by current course
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # ✅ Get current discounted price (accumulated from all coupons)
    if user.discounted_price:
        discounted_price = Decimal(str(user.discounted_price))
    else:
        discounted_price = course_price
    
    # ✅ Calculate total discount applied
    total_discount = course_price - discounted_price

    # ✅ Calculate amount_owed based on discounted_price
    amount_owed = max(Decimal('0.00'), discounted_price - total_paid)

    # Dynamic minimum payment (based on discounted price if applicable)
    min_payment = discounted_price * (Decimal('0.3') if discounted_price < 200000 else Decimal('0.4'))

    return Response({
        'course_price': float(course_price),
        'discounted_price': float(discounted_price),
        'discount_applied': float(total_discount),
        'amount_paid': float(total_paid),
        'amount_owed': float(amount_owed),
        'min_payment_required': float(min_payment),
    })


# ==========================================================
# INITIALIZE PAYMENT (with coupon + free payment support)
# ==========================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_payment(request):
    try:
        user = request.user

        if not user.course:
            return Response({'error': 'User has no assigned course.'}, status=400)

        # --------------------------
        # Parse amount
        # --------------------------
        try:
            amount_to_pay = Decimal(str(request.data.get('amount', 0)))
        except (InvalidOperation, TypeError):
            return Response({'error': 'Invalid payment amount.'}, status=400)

        if amount_to_pay < 0:
            return Response({'error': 'Invalid amount entered.'}, status=400)

        # --------------------------
        # Handle coupon
        # --------------------------
        coupon_code = request.data.get('coupon_code', '').strip()
        discount_applied = Decimal('0.00')
        course_price = Decimal(str(user.course.price))
        
        # ✅ Start with existing discounted price if available, else use course price
        if user.discounted_price:
            current_price = Decimal(str(user.discounted_price))
        else:
            current_price = course_price
        
        discounted_price = current_price
        coupon = None

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                if not coupon.is_valid():
                    return Response({'error': 'Coupon is not valid or expired.'}, status=400)

                # ✅ Apply discount to current price (which may already be discounted)
                new_discounted_price = coupon.apply_discount(current_price)
                discount_applied = current_price - new_discounted_price
                discounted_price = new_discounted_price

                # ✅ Persist the new discounted price to the user
                user.discounted_price = discounted_price
                user.save(update_fields=['discounted_price'])

            except Coupon.DoesNotExist:
                return Response({'error': 'Coupon code does not exist.'}, status=400)

        # --------------------------
        # Remaining balance - ✅ Only count payments for current course
        # --------------------------
        total_paid = Transaction.objects.filter(
            user=user, 
            status='success',
            course=user.course  # ✅ Filter by current course
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        remaining = discounted_price - total_paid

        if remaining <= 0:
            return Response({'message': 'You have fully paid for this course.'}, status=400)

        # --------------------------
        # Minimum first payment
        # --------------------------
        if course_price < 200000:
            min_payment = course_price * Decimal('0.3')
        else:
            min_payment = course_price * Decimal('0.4')
        min_payment = min(min_payment, discounted_price)

        if total_paid == 0 and amount_to_pay < min_payment and discounted_price > 0:
            return Response(
                {'error': f'First payment must be at least ₦{float(min_payment):,.2f}.'},
                status=400
            )

        # --------------------------
        # Prevent overpayment
        # --------------------------
        if amount_to_pay > remaining:
            return Response(
                {'error': f'You cannot pay more than your remaining balance of ₦{float(remaining):,.2f}.'},
                status=400
            )

        # --------------------------
        # Create transaction - ✅ Include course
        # --------------------------
        reference = f"TXN_{uuid.uuid4().hex[:12].upper()}"
        transaction = Transaction.objects.create(
            user=user,
            course=user.course,  # ✅ Track which course this payment is for
            reference=reference,
            email=user.email,
            amount=amount_to_pay,
            status='pending',
            metadata={
                'user_id': user.id,
                'user_name': user.name,
                'course_id': user.course.id,  # ✅ Store course ID
                'course_name': user.course.course_name,
                'coupon_code': coupon_code if coupon_code else None,
                'discount_applied': float(discount_applied),
                'discounted_price': float(discounted_price),
                'original_course_price': float(course_price),
            },
        )

        # --------------------------
        # ✅ Full coupon discount → skip Paystack and count as payment
        # --------------------------
        if discount_applied > 0 and (discounted_price == 0 or amount_to_pay == 0):
            transaction.status = "success"
            transaction.amount = discount_applied  # ✅ Record the discount as the amount
            transaction.paid_at = timezone.now()
            transaction.save()

            # ✅ Recalculate based on current course payments only
            total_paid_now = Transaction.objects.filter(
                user=user, 
                status='success',
                course=user.course
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            user.amount_paid = total_paid_now
            user.amount_owed = max(Decimal("0.00"), discounted_price - total_paid_now)
            user.next_due_date = timezone.now().date() + timezone.timedelta(days=30)
            user.save()

            # Generate receipt
            generate_receipt_pdf(transaction)

            # Increment coupon usage
            if coupon:
                coupon.times_used += 1
                coupon.save()

            return Response({
                "success": True,
                "message": "Coupon applied successfully!",
                "reference": reference,
                "authorization_url": None,
                "amount": float(discount_applied),
                "discount_applied": float(discount_applied),
                "discounted_price": float(discounted_price),
                "remaining_balance": float(user.amount_owed),
                "status": "success",
            })

        # --------------------------
        # Partial payment → initialize Paystack
        # --------------------------
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'email': user.email,
            'amount': int(amount_to_pay * 100),  # Kobo
            'reference': reference,
            'callback_url': f"{settings.FRONTEND_URL}/payment?reference={reference}",
            'metadata': transaction.metadata,  
    
        }

        res = requests.post(f'{settings.PAYSTACK_BASE_URL}/transaction/initialize', headers=headers, json=payload)
        data = res.json()

        if res.status_code == 200 and data.get('status'):
            # Increment coupon usage if applied
            if coupon:
                coupon.times_used += 1
                coupon.save()

            remaining_balance = float(remaining - amount_to_pay)

            return Response({
                'success': True,
                'authorization_url': data['data']['authorization_url'],
                'reference': reference,
                'amount': float(amount_to_pay),
                'discount_applied': float(discount_applied),
                'discounted_price': float(discounted_price),
                'remaining_balance': remaining_balance
            })

        # Fallback
        transaction.status = 'failed'
        transaction.save()
        return Response({'error': 'Payment initialization failed.'}, status=400)

    except Exception as e:
        import traceback
        print("🔥 Payment Init Error:", traceback.format_exc())
        return Response({'error': str(e)}, status=500)


# ==========================================================
# VERIFY PAYMENT
# ==========================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_payment(request, reference):
    try:
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        # Retry logic for transient SSL/network errors
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(
                    f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}",
                    headers=headers,
                    timeout=10
                )
                break
            except requests.exceptions.SSLError as ssl_err:
                if attempt < MAX_RETRIES - 1:
                    print(f"⚠️ SSL error, retrying {attempt+1}/{MAX_RETRIES}...", ssl_err)
                    import time; time.sleep(1)
                else:
                    raise
            except requests.exceptions.RequestException as req_err:
                if attempt < MAX_RETRIES - 1:
                    print(f"⚠️ Network error, retrying {attempt+1}/{MAX_RETRIES}...", req_err)
                    import time; time.sleep(1)
                else:
                    raise

        try:
            res_data = response.json() if response.content else {}
        except ValueError:
            print("⚠️ Invalid JSON from Paystack:", response.text)
            res_data = {}

        # If Paystack reports success
        if isinstance(res_data, dict) and res_data.get("data") and res_data["data"].get("status") == "success":
            transaction = Transaction.objects.get(reference=reference)
            user = transaction.user

            if transaction.status == "success":
                return Response({
                    "message": "Payment already verified.",
                    "amount_paid": float(user.amount_paid or 0),
                    "amount_owed": float(user.amount_owed or 0),
                    "status": transaction.status,
                }, status=status.HTTP_200_OK)

            metadata = parse_metadata(transaction.metadata)
            course_price = Decimal(str(user.course.price))
            discounted_price = Decimal(str(metadata.get('discounted_price') or user.discounted_price or course_price))
            discount_applied = Decimal(str(metadata.get('discount_applied', 0)))

            transaction.status = "success"
            transaction.paid_at = timezone.now()
            transaction.save()

            # ✅ Recalculate based on current course payments only
            total_paid = Transaction.objects.filter(
                user=user, 
                status='success',
                course=user.course
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            user.amount_paid = total_paid
            user.amount_owed = max(Decimal("0.00"), discounted_price - total_paid)
            user.next_due_date = timezone.now().date() + timezone.timedelta(days=30)

            if not user.discounted_price:
                user.discounted_price = discounted_price

            user.save()
            generate_receipt_pdf(transaction)

            print(
                f"✅ Payment verified for {user.email}: "
                f"Paid ₦{transaction.amount}, "
                f"Total Paid: ₦{total_paid}, "
                f"Course Price: ₦{course_price}, "
                f"Discounted Price: ₦{discounted_price}, "
                f"Discount Applied: ₦{discount_applied}, "
                f"Owed: ₦{user.amount_owed}"
            )

            return Response({
                "success": True,
                "message": "Payment verified successfully.",
                "amount_paid": float(user.amount_paid),
                "amount_owed": float(user.amount_owed),
                "discounted_price": float(discounted_price),
                "discount_applied": float(discount_applied),
                "status": transaction.status,
            }, status=status.HTTP_200_OK)

        else:
            print("⚠️ Verification failed or unexpected response:", res_data)
            return Response({
                "success": False,
                "message": "Payment verification failed.",
                "response": res_data,
            }, status=status.HTTP_400_BAD_REQUEST)

    except Transaction.DoesNotExist:
        return Response({"error": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        print("🔥 Verification error:", str(e))
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================================
# ADMIN DASHBOARD STATS
# ==========================================================
@api_view(['GET'])
@permission_classes([IsAdminUser])
def payment_statistics(request):
    """Get payment statistics for admin dashboard"""
    try:
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')

        queryset = Transaction.objects.all()
        if from_date:
            queryset = queryset.filter(created_at__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__lte=to_date)

        total_revenue = queryset.filter(status='success').aggregate(total=Sum('amount'))['total'] or 0
        successful_payments = queryset.filter(status='success').count()
        pending_payments = queryset.filter(status='pending').count()
        failed_payments = queryset.filter(status='failed').count()

        payment_type_breakdown = {}
        for item in PaymentItem.objects.all():
            transactions = Transaction.objects.filter(payment_items=item, status='success')
            total = transactions.aggregate(total=Sum('amount'))['total'] or 0
            if total > 0:
                payment_type_breakdown[item.payment_type] = {
                    'name': item.name,
                    'total': float(total),
                    'count': transactions.count(),
                }

        return Response({
            'total_revenue': float(total_revenue),
            'successful_payments': successful_payments,
            'pending_payments': pending_payments,
            'failed_payments': failed_payments,
            'total_transactions': queryset.count(),
            'total_users': CustomUser.objects.filter(is_staff=False).count(),
            'payment_type_breakdown': payment_type_breakdown,
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================================
# PAYSTACK WEBHOOK
# ==========================================================
@csrf_exempt
def paystack_webhook(request):
    import json
    from decimal import Decimal
    from django.utils import timezone
    from django.db.models import Sum

    try:
        payload = json.loads(request.body)
        event = payload.get("event")

        if event != "charge.success":
            print("Webhook ignored, event:", event)
            return JsonResponse({"status": "ignored"}, status=200)

        data = payload.get("data", {})
        reference = data.get("reference")

        if not reference:
            print("Webhook missing reference")
            return JsonResponse({"error": "Missing reference"}, status=400)

        transaction = Transaction.objects.filter(reference=reference).first()
        if not transaction:
            print(f"⚠️ Transaction {reference} not found in database.")
            return JsonResponse({"message": "Transaction not found."}, status=404)

        if transaction.status == "success":
            print(f"⚠️ Transaction {reference} already processed.")
            return JsonResponse({"message": "Transaction already processed."}, status=200)

        user = transaction.user
        course_price = Decimal(str(user.course.price or 0))

        metadata = parse_metadata(transaction.metadata)

        if metadata.get('discounted_price'):
            discounted_price = Decimal(str(metadata.get('discounted_price')))
        elif user.discounted_price:
            discounted_price = Decimal(str(user.discounted_price))
        else:
            discounted_price = course_price

        discount_applied = Decimal(str(metadata.get('discount_applied', 0)))

        transaction.amount = Decimal(str(data.get("amount", 0))) / 100
        transaction.status = "success"
        transaction.paid_at = timezone.now()
        transaction.save(update_fields=['amount', 'status', 'paid_at'])

        # ✅ Recalculate based on current course payments only
        total_paid = Transaction.objects.filter(
            user=user, 
            status='success',
            course=user.course
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        user.amount_paid = total_paid
        user.amount_owed = max(Decimal("0.00"), discounted_price - total_paid)
        user.next_due_date = timezone.now().date() + timezone.timedelta(days=30)

        if not user.discounted_price:
            user.discounted_price = discounted_price

        user.save(update_fields=['amount_paid', 'amount_owed', 'next_due_date', 'discounted_price'])

        generate_receipt_pdf(transaction)

        print(
            f"🔔 Webhook processed: {user.email} paid ₦{transaction.amount} | "
            f"Total Paid: ₦{total_paid} | "
            f"Course Price: ₦{course_price} | "
            f"Discounted Price: ₦{discounted_price} | "
            f"Discount: ₦{discount_applied} | "
            f"Owed: ₦{user.amount_owed}"
        )

        return JsonResponse({"status": "success"}, status=200)

    except Exception as e:
        import traceback
        print("🔥 Webhook error:", str(e))
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)


# ==========================================================
# TRANSACTION VIEWSET
# ==========================================================
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.all()

        if not self.request.user.is_staff:
            # ✅ Filter by current course for students
            queryset = queryset.filter(user=self.request.user, course=self.request.user.course)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.select_related('user', 'course').prefetch_related('payment_items')


class StudentTransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # ✅ Only show transactions for current course
        return Transaction.objects.filter(user=user, course=user.course).order_by('-paid_at')


def download_receipt(request, reference):
    try:
        receipt = PaymentReceipt.objects.get(transaction__reference=reference)
        file_path = receipt.pdf_file.path

        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=f"{reference}_receipt.pdf"
        )

    except PaymentReceipt.DoesNotExist:
        raise Http404("Receipt not found")