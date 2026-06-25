import { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import axios from 'axios';
import { config } from '../../config/api.config';

// Initialize Stripe with publishable key
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || 'pk_test_xxxxx');

// Card element styling - Dark theme
const CARD_ELEMENT_OPTIONS = {
  hidePostalCode: true, // Remove postal code field
  style: {
    base: {
      fontSize: '16px',
      color: '#ffffff',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      '::placeholder': {
        color: '#94a3b8',
      },
      padding: '10px 12px',
      backgroundColor: 'transparent',
    },
    invalid: {
      color: '#f87171',
      iconColor: '#f87171',
    },
  },
};

/**
 * Checkout Form Component
 * Handles the actual Stripe payment form and submission
 */
function CheckoutForm({ planId, billingCycle, onSuccess, onError }) {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cardComplete, setCardComplete] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    if (!cardComplete) {
      setError('Please complete your card information');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');

      // Step 1: Create payment intent on backend
      const { data } = await axios.post(
        config.STRIPE_CREATE_INTENT_URL,
        {
          plan_id: planId,
          billing_cycle: billingCycle
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // Step 2: Confirm card payment with Stripe
      const result = await stripe.confirmCardPayment(data.clientSecret, {
        payment_method: {
          card: elements.getElement(CardElement),
        },
      });

      if (result.error) {
        // Payment failed
        setError(result.error.message);
        if (onError) onError(result.error);
        setLoading(false);
        return;
      }

      // Step 3: Confirm with backend
      const confirmResponse = await axios.post(
        config.STRIPE_CONFIRM_URL,
        {
          payment_intent_id: result.paymentIntent.id
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // Payment successful
      setLoading(false);
      if (onSuccess) {
        onSuccess(confirmResponse.data);
      } else {
        alert('Payment successful!');
        window.location.href = '/dashboard';
      }
    } catch (err) {
      console.error('Stripe payment error:', err);
      const errorMsg = err.response?.data?.error || err.message || 'Payment failed. Please try again.';
      setError(errorMsg);
      if (onError) onError(err);
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="stripe-form space-y-4">
      {/* Card Element Container */}
      <div className="border border-gray-600 rounded-lg p-4 bg-[#0f172a]">
        <label htmlFor="card-element" className="block text-sm font-medium text-white mb-2">
          Card Information
        </label>
        <CardElement
          id="card-element"
          options={CARD_ELEMENT_OPTIONS}
          onChange={(e) => {
            setCardComplete(e.complete);
            if (e.error) {
              setError(e.error.message);
            } else {
              setError(null);
            }
          }}
        />
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-900/30 border border-red-500/50 rounded-lg">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Secure Badge */}
      <div className="flex items-center justify-center text-sm text-gray-400">
        <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
        </svg>
        <span>Secure payment powered by Stripe</span>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={!stripe || loading || !cardComplete}
        className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium
                   hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed
                   transition-colors duration-200 flex items-center justify-center"
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            Processing...
          </>
        ) : (
          `Pay Now`
        )}
      </button>

      {/* Test Cards Info (only show in dev) */}
      {import.meta.env.DEV && (
        <div className="mt-4 p-3 bg-blue-900/30 border border-blue-500/50 rounded-lg">
          <p className="text-xs text-blue-400 font-medium mb-1">Test Card Numbers:</p>
          <p className="text-xs text-blue-300">4242 4242 4242 4242 - Success</p>
          <p className="text-xs text-blue-300">4000 0000 0000 9995 - Declined</p>
          <p className="text-xs text-blue-300 mt-1">Use any future date, any 3-digit CVC</p>
        </div>
      )}
    </form>
  );
}

/**
 * Stripe Checkout Component
 * Wraps CheckoutForm with Stripe Elements provider
 *
 * @param {Object} props
 * @param {string} props.planId - UUID of the pricing plan
 * @param {string} props.billingCycle - "MONTHLY" or "YEARLY"
 * @param {Function} props.onSuccess - Callback when payment succeeds
 * @param {Function} props.onError - Callback when payment fails
 */
export default function StripeCheckout({ planId, billingCycle = 'MONTHLY', onSuccess, onError }) {
  return (
    <div className="stripe-checkout">
      <Elements stripe={stripePromise}>
        <CheckoutForm
          planId={planId}
          billingCycle={billingCycle}
          onSuccess={onSuccess}
          onError={onError}
        />
      </Elements>
    </div>
  );
}
