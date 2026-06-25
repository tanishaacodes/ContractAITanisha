"""
Payment Gateway Views for ContractAI
Handles Stripe and PayPal payment processing for subscription plans.
"""

import json
import stripe
from decimal import Decimal
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .paypal_client import paypal_client
from core.models import User, PricingPlan, PaymentTransaction, Subscription
from core.authentication import JWTAuthentication

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# =========================
# PAYPAL PAYMENT ENDPOINTS
# =========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_paypal_order(request):
    """
    Create a PayPal order for subscription payment.

    Request body:
    {
        "plan_id": "uuid",
        "billing_cycle": "MONTHLY" or "YEARLY"
    }
    """
    try:
        data = request.data
        plan_id = data.get('plan_id')
        billing_cycle = data.get('billing_cycle', 'MONTHLY')

        # Get the pricing plan
        try:
            plan = PricingPlan.objects.get(id=plan_id)
        except PricingPlan.DoesNotExist:
            return JsonResponse({
                'error': 'Pricing plan not found'
            }, status=404)

        # Calculate amount based on billing cycle
        amount = str(plan.price_monthly)
        if billing_cycle == 'YEARLY':
            amount = str(plan.price_monthly * 12)

        # Create PayPal order
        order = OrdersCreateRequest()
        order.prefer('return=representation')
        order.request_body({
            "intent": "CAPTURE",
            "purchase_units": [{
                "description": f"{plan.display_name} - {billing_cycle}",
                "amount": {
                    "currency_code": "USD",
                    "value": amount
                },
                "reference_id": str(request.user.id)
            }],
            "application_context": {
                "brand_name": "ContractAI",
                "landing_page": "BILLING",
                "user_action": "PAY_NOW",
                "return_url": f"{request.scheme}://{request.get_host()}/api/payments/paypal/success",
                "cancel_url": f"{request.scheme}://{request.get_host()}/api/payments/paypal/cancel"
            }
        })

        response = paypal_client().execute(order)
        order_id = response.result.id

        # Create payment transaction record
        transaction = PaymentTransaction.objects.create(
            user=request.user,
            plan=plan,
            payment_method='PAYPAL',
            amount=Decimal(amount),
            currency='USD',
            status='PENDING',
            paypal_order_id=order_id,
            description=f"{plan.display_name} subscription - {billing_cycle}"
        )

        return JsonResponse({
            'orderID': order_id,
            'transaction_id': transaction.id
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def capture_paypal_order(request):
    """
    Capture (complete) a PayPal order after user approval.

    Request body:
    {
        "orderID": "paypal_order_id"
    }
    """
    try:
        data = request.data
        order_id = data.get('orderID')

        if not order_id:
            return JsonResponse({
                'error': 'Order ID is required'
            }, status=400)

        # Capture the order
        capture = OrdersCaptureRequest(order_id)
        response = paypal_client().execute(capture)

        # Update transaction record
        try:
            transaction = PaymentTransaction.objects.get(
                paypal_order_id=order_id,
                user=request.user
            )
            transaction.status = 'COMPLETED'
            transaction.completed_at = timezone.now()
            transaction.gateway_response = response.result.__dict__
            transaction.save()

            # Activate subscription
            _activate_subscription(
                user=request.user,
                plan=transaction.plan,
                transaction=transaction,
                payment_method='PAYPAL',
                billing_cycle='MONTHLY'  # You may want to store this in transaction
            )

            # Update user's current plan
            request.user.current_plan = transaction.plan
            request.user.save()

            return JsonResponse({
                'status': 'COMPLETED',
                'transaction_id': transaction.id,
                'order_id': order_id
            })

        except PaymentTransaction.DoesNotExist:
            return JsonResponse({
                'error': 'Transaction not found'
            }, status=404)

    except Exception as e:
        # Mark transaction as failed
        if order_id:
            PaymentTransaction.objects.filter(
                paypal_order_id=order_id,
                user=request.user
            ).update(
                status='FAILED',
                failure_reason=str(e)
            )

        return JsonResponse({
            'error': str(e)
        }, status=500)


# =========================
# STRIPE PAYMENT ENDPOINTS
# =========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_stripe_payment_intent(request):
    """
    Create a Stripe Payment Intent for subscription payment.

    Request body:
    {
        "plan_id": "uuid",
        "billing_cycle": "MONTHLY" or "YEARLY"
    }
    """
    try:
        data = request.data
        plan_id = data.get('plan_id')
        billing_cycle = data.get('billing_cycle', 'MONTHLY')

        # Get the pricing plan
        try:
            plan = PricingPlan.objects.get(id=plan_id)
        except PricingPlan.DoesNotExist:
            return JsonResponse({
                'error': 'Pricing plan not found'
            }, status=404)

        # Calculate amount based on billing cycle (Stripe expects amount in cents)
        amount = int(plan.price_monthly * 100)
        if billing_cycle == 'YEARLY':
            amount = int(plan.price_monthly * 12 * 100)

        # Create Stripe Payment Intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            automatic_payment_methods={"enabled": True},
            metadata={
                "user_id": str(request.user.id),
                "plan_id": str(plan_id),
                "billing_cycle": billing_cycle
            },
            description=f"{plan.display_name} - {billing_cycle}"
        )

        # Create payment transaction record
        transaction = PaymentTransaction.objects.create(
            user=request.user,
            plan=plan,
            payment_method='STRIPE',
            amount=Decimal(amount) / 100,  # Convert cents back to dollars
            currency='USD',
            status='PENDING',
            stripe_payment_intent_id=intent.id,
            description=f"{plan.display_name} subscription - {billing_cycle}"
        )

        return JsonResponse({
            'clientSecret': intent.client_secret,
            'publishableKey': settings.STRIPE_PUBLISHABLE_KEY,
            'transaction_id': transaction.id
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_stripe_payment(request):
    """
    Confirm a Stripe payment after successful card authorization.
    This endpoint is called after the frontend confirms the payment with Stripe.

    Request body:
    {
        "payment_intent_id": "stripe_payment_intent_id"
    }
    """
    try:
        data = request.data
        payment_intent_id = data.get('payment_intent_id')

        if not payment_intent_id:
            return JsonResponse({
                'error': 'Payment Intent ID is required'
            }, status=400)

        # Retrieve payment intent from Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        # Update transaction record
        try:
            transaction = PaymentTransaction.objects.get(
                stripe_payment_intent_id=payment_intent_id,
                user=request.user
            )

            if intent.status == 'succeeded':
                transaction.status = 'COMPLETED'
                transaction.completed_at = timezone.now()
                transaction.gateway_response = intent
                transaction.save()

                # Activate subscription
                billing_cycle = intent.metadata.get('billing_cycle', 'MONTHLY')
                _activate_subscription(
                    user=request.user,
                    plan=transaction.plan,
                    transaction=transaction,
                    payment_method='STRIPE',
                    billing_cycle=billing_cycle
                )

                # Update user's current plan
                request.user.current_plan = transaction.plan
                request.user.save()

                return JsonResponse({
                    'status': 'COMPLETED',
                    'transaction_id': transaction.id
                })
            else:
                transaction.status = 'FAILED'
                transaction.failure_reason = f"Payment status: {intent.status}"
                transaction.save()

                return JsonResponse({
                    'error': f'Payment failed with status: {intent.status}'
                }, status=400)

        except PaymentTransaction.DoesNotExist:
            return JsonResponse({
                'error': 'Transaction not found'
            }, status=404)

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


# =========================
# WEBHOOK HANDLERS
# =========================

@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events for payment verification and subscription updates.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Handle different event types
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        _handle_stripe_payment_success(payment_intent)

    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        _handle_stripe_payment_failure(payment_intent)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        _handle_stripe_subscription_cancelled(subscription)

    return JsonResponse({'status': 'success'})


@csrf_exempt
@require_http_methods(["POST"])
def paypal_webhook(request):
    """
    Handle PayPal webhook events for payment verification.
    Note: PayPal webhook verification requires additional setup.
    """
    try:
        data = json.loads(request.body)
        event_type = data.get('event_type')

        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            # Handle successful payment capture
            resource = data.get('resource', {})
            order_id = resource.get('id')

            if order_id:
                transaction = PaymentTransaction.objects.filter(
                    paypal_order_id=order_id
                ).first()

                if transaction and transaction.status != 'COMPLETED':
                    transaction.status = 'COMPLETED'
                    transaction.completed_at = timezone.now()
                    transaction.gateway_response = data
                    transaction.save()

        elif event_type == 'PAYMENT.CAPTURE.DENIED':
            # Handle failed payment
            resource = data.get('resource', {})
            order_id = resource.get('id')

            if order_id:
                PaymentTransaction.objects.filter(
                    paypal_order_id=order_id
                ).update(
                    status='FAILED',
                    failure_reason='Payment denied by PayPal'
                )

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =========================
# PAYMENT HISTORY & INFO
# =========================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_history(request):
    """
    Get payment transaction history for the current user.
    """
    try:
        transactions = PaymentTransaction.objects.filter(
            user=request.user
        ).select_related('plan').order_by('-created_at')

        transaction_data = [{
            'id': t.id,
            'plan': {
                'id': t.plan.id,
                'name': t.plan.display_name,
                'price': str(t.plan.price_monthly)
            },
            'payment_method': t.payment_method,
            'amount': str(t.amount),
            'currency': t.currency,
            'status': t.status,
            'description': t.description,
            'created_at': t.created_at.isoformat(),
            'completed_at': t.completed_at.isoformat() if t.completed_at else None
        } for t in transactions]

        return JsonResponse({
            'transactions': transaction_data
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_subscription(request):
    """
    Get the current active subscription for the user.
    """
    try:
        subscription = Subscription.objects.filter(
            user=request.user,
            status='ACTIVE'
        ).select_related('plan').first()

        if not subscription:
            return JsonResponse({
                'subscription': None,
                'message': 'No active subscription found'
            })

        return JsonResponse({
            'subscription': {
                'id': subscription.id,
                'plan': {
                    'id': subscription.plan.id,
                    'name': subscription.plan.display_name,
                    'price': str(subscription.plan.price_monthly),
                    'contract_limit': subscription.plan.contract_limit
                },
                'status': subscription.status,
                'billing_cycle': subscription.billing_cycle,
                'current_period_start': subscription.current_period_start.isoformat(),
                'current_period_end': subscription.current_period_end.isoformat(),
                'auto_renew': subscription.auto_renew
            }
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


# =========================
# HELPER FUNCTIONS
# =========================

def _activate_subscription(user, plan, transaction, payment_method, billing_cycle='MONTHLY'):
    """
    Create or update subscription after successful payment.
    """
    # Deactivate any existing active subscriptions
    Subscription.objects.filter(
        user=user,
        status='ACTIVE'
    ).update(
        status='CANCELLED',
        cancelled_at=timezone.now()
    )

    # Calculate subscription dates
    start_date = timezone.now()
    if billing_cycle == 'YEARLY':
        end_date = start_date + timedelta(days=365)
    else:
        end_date = start_date + timedelta(days=30)

    # Create new subscription
    subscription = Subscription.objects.create(
        user=user,
        plan=plan,
        status='ACTIVE',
        billing_cycle=billing_cycle,
        start_date=start_date,
        current_period_start=start_date,
        current_period_end=end_date,
        auto_renew=True
    )

    if payment_method == 'STRIPE' and transaction.stripe_payment_intent_id:
        subscription.stripe_subscription_id = transaction.stripe_payment_intent_id
        subscription.save()
    elif payment_method == 'PAYPAL' and transaction.paypal_order_id:
        subscription.paypal_subscription_id = transaction.paypal_order_id
        subscription.save()

    return subscription


def _handle_stripe_payment_success(payment_intent):
    """Handle successful Stripe payment from webhook."""
    payment_intent_id = payment_intent.get('id')

    transaction = PaymentTransaction.objects.filter(
        stripe_payment_intent_id=payment_intent_id
    ).first()

    if transaction and transaction.status != 'COMPLETED':
        transaction.status = 'COMPLETED'
        transaction.completed_at = timezone.now()
        transaction.gateway_response = payment_intent
        transaction.save()


def _handle_stripe_payment_failure(payment_intent):
    """Handle failed Stripe payment from webhook."""
    payment_intent_id = payment_intent.get('id')

    PaymentTransaction.objects.filter(
        stripe_payment_intent_id=payment_intent_id
    ).update(
        status='FAILED',
        failure_reason=payment_intent.get('last_payment_error', {}).get('message', 'Payment failed')
    )


def _handle_stripe_subscription_cancelled(subscription_data):
    """Handle Stripe subscription cancellation from webhook."""
    subscription_id = subscription_data.get('id')

    Subscription.objects.filter(
        stripe_subscription_id=subscription_id
    ).update(
        status='CANCELLED',
        cancelled_at=timezone.now(),
        auto_renew=False
    )
