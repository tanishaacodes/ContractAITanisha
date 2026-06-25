# Payment Integration Guide - ContractAI MVP

This document provides a comprehensive guide to the Stripe and PayPal payment integration for ContractAI.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup Instructions](#setup-instructions)
4. [API Endpoints](#api-endpoints)
5. [Frontend Integration](#frontend-integration)
6. [Webhook Configuration](#webhook-configuration)
7. [Testing](#testing)
8. [Production Deployment](#production-deployment)

---

## Overview

ContractAI supports two payment gateways:

- **PayPal**: Wallet payments + PayPal balance (200+ countries)
- **Stripe**: Credit/Debit cards - Visa, Mastercard, Amex (135+ countries)

### Features

- One-time payments for subscription plans (Free, Standard, Professional)
- Secure payment processing with server-side verification
- Payment transaction history
- Webhook support for payment verification
- Subscription management

---

## Architecture

```
React/Next.js Frontend
├── PayPal JS SDK
├── Stripe Elements
↓
Django Backend (Python)
├── PayPal Orders API
├── Stripe Payment Intents
├── Payment Models (Database)
└── Webhook Verification
```

---

## Setup Instructions

### 1. Install Required Packages

Already installed:
```bash
pip install stripe paypal-checkout-serversdk python-dotenv
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

#### Get PayPal Credentials

1. Go to [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/)
2. Create a new app
3. Copy your `Client ID` and `Secret`
4. For testing: Use **Sandbox** credentials
5. For production: Use **Live** credentials

```env
PAYPAL_CLIENT_ID=YOUR_PAYPAL_CLIENT_ID_HERE
PAYPAL_CLIENT_SECRET=YOUR_PAYPAL_CLIENT_SECRET_HERE
PAYPAL_MODE=sandbox  # or 'live' for production
```

#### Get Stripe Credentials

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Copy your API keys
3. For testing: Use keys starting with `sk_test_` and `pk_test_`
4. For production: Use keys starting with `sk_live_` and `pk_live_`

```env
STRIPE_SECRET_KEY=sk_test_YOUR_STRIPE_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_STRIPE_PUBLISHABLE_KEY_HERE
```

### 3. Run Database Migrations

The payment models have already been migrated. If you need to recreate:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## API Endpoints

### PayPal Endpoints

#### 1. Create PayPal Order
**POST** `/api/payments/paypal/create-order`

Creates a PayPal order for subscription payment.

**Request:**
```json
{
  "plan_id": "uuid-of-pricing-plan",
  "billing_cycle": "MONTHLY"
}
```

**Response:**
```json
{
  "orderID": "paypal_order_id",
  "transaction_id": "uuid"
}
```

**Headers:** `Authorization: Bearer <jwt_token>`

---

#### 2. Capture PayPal Order
**POST** `/api/payments/paypal/capture-order`

Completes the PayPal payment after user approval.

**Request:**
```json
{
  "orderID": "paypal_order_id"
}
```

**Response:**
```json
{
  "status": "COMPLETED",
  "transaction_id": "uuid",
  "order_id": "paypal_order_id"
}
```

---

### Stripe Endpoints

#### 3. Create Stripe Payment Intent
**POST** `/api/payments/stripe/create-intent`

Creates a Stripe Payment Intent for card payment.

**Request:**
```json
{
  "plan_id": "uuid-of-pricing-plan",
  "billing_cycle": "MONTHLY"
}
```

**Response:**
```json
{
  "clientSecret": "pi_xxx_secret_xxx",
  "publishableKey": "pk_test_xxx",
  "transaction_id": "uuid"
}
```

---

#### 4. Confirm Stripe Payment
**POST** `/api/payments/stripe/confirm`

Confirms payment after successful card authorization.

**Request:**
```json
{
  "payment_intent_id": "pi_xxx"
}
```

**Response:**
```json
{
  "status": "COMPLETED",
  "transaction_id": "uuid"
}
```

---

### Payment Information Endpoints

#### 5. Get Payment History
**GET** `/api/payments/history`

Returns all payment transactions for the current user.

**Response:**
```json
{
  "transactions": [
    {
      "id": "uuid",
      "plan": {
        "id": "uuid",
        "name": "Professional Plan",
        "price": "30.00"
      },
      "payment_method": "STRIPE",
      "amount": "30.00",
      "currency": "USD",
      "status": "COMPLETED",
      "description": "Professional Plan subscription - MONTHLY",
      "created_at": "2026-01-08T10:30:00Z",
      "completed_at": "2026-01-08T10:31:00Z"
    }
  ]
}
```

---

#### 6. Get Current Subscription
**GET** `/api/subscription/current`

Returns the user's active subscription.

**Response:**
```json
{
  "subscription": {
    "id": "uuid",
    "plan": {
      "id": "uuid",
      "name": "Professional Plan",
      "price": "30.00",
      "contract_limit": 120
    },
    "status": "ACTIVE",
    "billing_cycle": "MONTHLY",
    "current_period_start": "2026-01-08T10:30:00Z",
    "current_period_end": "2026-02-08T10:30:00Z",
    "auto_renew": true
  }
}
```

---

## Frontend Integration

### PayPal Integration (React/Next.js)

#### 1. Load PayPal SDK

Add to your HTML `<head>`:
```html
<script src="https://www.paypal.com/sdk/js?client-id=YOUR_CLIENT_ID&currency=USD"></script>
```

#### 2. PayPal Button Component

```javascript
import { useEffect, useRef } from 'react';
import axios from 'axios';

export default function PayPalButton({ planId, billingCycle }) {
  const paypalRef = useRef();

  useEffect(() => {
    if (window.paypal) {
      window.paypal.Buttons({
        createOrder: async () => {
          const response = await axios.post(
            'http://localhost:8000/api/payments/paypal/create-order',
            {
              plan_id: planId,
              billing_cycle: billingCycle
            },
            {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            }
          );
          return response.data.orderID;
        },
        onApprove: async (data) => {
          await axios.post(
            'http://localhost:8000/api/payments/paypal/capture-order',
            {
              orderID: data.orderID
            },
            {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            }
          );
          alert('Payment successful!');
          window.location.href = '/dashboard';
        },
        onError: (err) => {
          console.error('PayPal error:', err);
          alert('Payment failed. Please try again.');
        }
      }).render(paypalRef.current);
    }
  }, [planId, billingCycle]);

  return <div ref={paypalRef}></div>;
}
```

---

### Stripe Integration (React/Next.js)

#### 1. Install Stripe Libraries

```bash
npm install @stripe/react-stripe-js @stripe/stripe-js
```

#### 2. Stripe Checkout Component

```javascript
import { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import axios from 'axios';

const stripePromise = loadStripe('pk_test_YOUR_PUBLISHABLE_KEY');

function CheckoutForm({ planId, billingCycle }) {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);

    try {
      // Create payment intent
      const { data } = await axios.post(
        'http://localhost:8000/api/payments/stripe/create-intent',
        {
          plan_id: planId,
          billing_cycle: billingCycle
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      // Confirm card payment
      const result = await stripe.confirmCardPayment(data.clientSecret, {
        payment_method: {
          card: elements.getElement(CardElement)
        }
      });

      if (result.error) {
        alert(result.error.message);
      } else {
        // Confirm with backend
        await axios.post(
          'http://localhost:8000/api/payments/stripe/confirm',
          {
            payment_intent_id: result.paymentIntent.id
          },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        );
        alert('Payment successful!');
        window.location.href = '/dashboard';
      }
    } catch (error) {
      console.error('Payment error:', error);
      alert('Payment failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <CardElement />
      <button type="submit" disabled={!stripe || loading}>
        {loading ? 'Processing...' : 'Pay Now'}
      </button>
    </form>
  );
}

export default function StripeCheckout({ planId, billingCycle }) {
  return (
    <Elements stripe={stripePromise}>
      <CheckoutForm planId={planId} billingCycle={billingCycle} />
    </Elements>
  );
}
```

---

## Webhook Configuration

Webhooks ensure payment verification and handle subscription events.

### Stripe Webhooks

1. Go to [Stripe Webhooks Dashboard](https://dashboard.stripe.com/webhooks)
2. Click **Add endpoint**
3. Enter your webhook URL: `https://yourdomain.com/api/payments/stripe/webhook`
4. Select events to listen to:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.subscription.deleted`
5. Copy the **Signing secret** and add to `.env`:
   ```env
   STRIPE_WEBHOOK_SECRET=whsec_xxxxx
   ```

### PayPal Webhooks

1. Go to [PayPal Webhooks](https://developer.paypal.com/dashboard/webhooks)
2. Create a new webhook
3. Enter URL: `https://yourdomain.com/api/payments/paypal/webhook`
4. Select events:
   - `PAYMENT.CAPTURE.COMPLETED`
   - `PAYMENT.CAPTURE.DENIED`

---

## Testing

### Test Payment Methods

#### PayPal Sandbox Testing

1. Create test accounts at [PayPal Sandbox](https://developer.paypal.com/dashboard/accounts)
2. Use sandbox credentials in `.env`
3. Log in with test buyer account during checkout

#### Stripe Test Cards

Use these test card numbers in **test mode**:

| Card Number | Description |
|-------------|-------------|
| `4242 4242 4242 4242` | Visa - Success |
| `4000 0025 0000 3155` | Visa - Requires 3D Secure |
| `4000 0000 0000 9995` | Visa - Declined |

- Any future expiry date (e.g., `12/34`)
- Any 3-digit CVC (e.g., `123`)
- Any postal code

### Testing Workflow

1. **Create a test user** via registration
2. **Get pricing plans** from `/api/pricing/plans`
3. **Initiate payment** with PayPal or Stripe
4. **Complete payment** using test credentials/cards
5. **Verify subscription** via `/api/subscription/current`
6. **Check payment history** via `/api/payments/history`

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Switch to **live** PayPal credentials
- [ ] Switch to **live** Stripe keys (sk_live_, pk_live_)
- [ ] Configure production webhook endpoints
- [ ] Set `PAYPAL_MODE=live` in production `.env`
- [ ] Enable HTTPS (required for payment gateways)
- [ ] Test payment flow end-to-end in production
- [ ] Set up error monitoring (Sentry, etc.)

### Security Best Practices

1. **Never expose secret keys** in frontend code
2. **Always verify webhooks** using signatures
3. **Use HTTPS** for all payment endpoints
4. **Validate amounts** on the server side
5. **Log all payment transactions** for auditing
6. **Implement rate limiting** on payment endpoints
7. **Monitor for fraud** and suspicious activity

---

## Supported Payment Coverage

| Method | Countries | Notes |
|--------|-----------|-------|
| PayPal | 200+ | Wallet, PayPal balance |
| Stripe Cards | 135+ | Visa, Mastercard, Amex |
| Apple Pay | Global | Auto-enabled via Stripe |
| Google Pay | Global | Auto-enabled via Stripe |

---

## Support & Troubleshooting

### Common Issues

**Issue**: "PayPal order creation failed"
- **Solution**: Check PayPal credentials in `.env`
- Ensure `PAYPAL_MODE` matches your credentials (sandbox/live)

**Issue**: "Stripe payment failed - Invalid API key"
- **Solution**: Verify `STRIPE_SECRET_KEY` in `.env`
- Ensure you're using the correct key for your environment

**Issue**: "Webhook signature verification failed"
- **Solution**: Check `STRIPE_WEBHOOK_SECRET` matches the one in Stripe dashboard
- Ensure webhook URL is publicly accessible (use ngrok for local testing)

### Webhook Testing (Local Development)

Use **ngrok** to expose your local server:

```bash
ngrok http 8000
```

Then use the ngrok URL for webhook configuration:
```
https://abc123.ngrok.io/api/payments/stripe/webhook
```

---

## API Reference Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/payments/paypal/create-order` | POST | Yes | Create PayPal order |
| `/api/payments/paypal/capture-order` | POST | Yes | Capture PayPal payment |
| `/api/payments/stripe/create-intent` | POST | Yes | Create Stripe payment intent |
| `/api/payments/stripe/confirm` | POST | Yes | Confirm Stripe payment |
| `/api/payments/stripe/webhook` | POST | No | Stripe webhook handler |
| `/api/payments/paypal/webhook` | POST | No | PayPal webhook handler |
| `/api/payments/history` | GET | Yes | Get payment history |
| `/api/subscription/current` | GET | Yes | Get current subscription |

---

## Database Schema

### PaymentTransaction Model

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user | ForeignKey | User who made payment |
| plan | ForeignKey | Pricing plan purchased |
| payment_method | String | STRIPE or PAYPAL |
| amount | Decimal | Payment amount |
| currency | String | Currency code (USD) |
| status | String | Payment status |
| stripe_payment_intent_id | String | Stripe payment ID |
| paypal_order_id | String | PayPal order ID |
| gateway_response | JSON | Full gateway response |
| created_at | DateTime | Creation timestamp |
| completed_at | DateTime | Completion timestamp |

### Subscription Model

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user | ForeignKey | Subscriber |
| plan | ForeignKey | Active plan |
| status | String | ACTIVE, CANCELLED, etc. |
| billing_cycle | String | MONTHLY or YEARLY |
| current_period_start | DateTime | Billing period start |
| current_period_end | DateTime | Billing period end |
| auto_renew | Boolean | Auto-renewal status |

---

**Version**: 1.0
**Last Updated**: January 8, 2026
**Contact**: support@contractai.com
