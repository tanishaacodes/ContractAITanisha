import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { config } from '../../config/api.config';

/**
 * PayPal Payment Button Component
 * Handles PayPal payment flow for subscription plans
 *
 * @param {Object} props
 * @param {string} props.planId - UUID of the pricing plan
 * @param {string} props.billingCycle - "MONTHLY" or "YEARLY"
 * @param {Function} props.onSuccess - Callback when payment succeeds
 * @param {Function} props.onError - Callback when payment fails
 */
export default function PayPalButton({ planId, billingCycle = 'MONTHLY', onSuccess, onError }) {
  const paypalRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load PayPal SDK script
    const loadPayPalScript = () => {
      // Check if script is already loaded
      if (window.paypal) {
        initializePayPalButton();
        return;
      }

      // Create script element
      const script = document.createElement('script');
      script.src = `https://www.paypal.com/sdk/js?client-id=${import.meta.env.VITE_PAYPAL_CLIENT_ID}&currency=USD`;
      script.async = true;
      script.onload = () => {
        setIsLoading(false);
        initializePayPalButton();
      };
      script.onerror = () => {
        setError('Failed to load PayPal SDK');
        setIsLoading(false);
        if (onError) onError(new Error('Failed to load PayPal SDK'));
      };

      document.body.appendChild(script);
    };

    const initializePayPalButton = () => {
      if (!window.paypal || !paypalRef.current) return;

      // Clear any existing buttons
      paypalRef.current.innerHTML = '';

      try {
        window.paypal.Buttons({
          // Create order on backend
          createOrder: async () => {
            try {
              const token = localStorage.getItem('token');
              const response = await axios.post(
                config.PAYPAL_CREATE_ORDER_URL,
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

              return response.data.orderID;
            } catch (err) {
              console.error('Error creating PayPal order:', err);
              setError(err.response?.data?.error || 'Failed to create order');
              if (onError) onError(err);
              throw err;
            }
          },

          // Capture payment after user approval
          onApprove: async (data) => {
            try {
              const token = localStorage.getItem('token');
              const response = await axios.post(
                config.PAYPAL_CAPTURE_ORDER_URL,
                {
                  orderID: data.orderID
                },
                {
                  headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                  }
                }
              );

              // Payment successful
              if (onSuccess) {
                onSuccess(response.data);
              } else {
                alert('Payment successful!');
                window.location.href = '/dashboard';
              }
            } catch (err) {
              console.error('Error capturing PayPal payment:', err);
              const errorMsg = err.response?.data?.error || 'Payment failed';
              setError(errorMsg);
              if (onError) {
                onError(err);
              } else {
                alert(`Payment failed: ${errorMsg}`);
              }
            }
          },

          // Handle errors
          onError: (err) => {
            console.error('PayPal error:', err);
            const errorMsg = 'Payment failed. Please try again.';
            setError(errorMsg);
            if (onError) {
              onError(err);
            } else {
              alert(errorMsg);
            }
          },

          // Handle user cancellation
          onCancel: () => {
            console.log('Payment cancelled by user');
            setError('Payment cancelled');
          },

          // Button styling
          style: {
            layout: 'vertical',
            color: 'blue',
            shape: 'rect',
            label: 'paypal'
          }
        }).render(paypalRef.current);

        setIsLoading(false);
      } catch (err) {
        console.error('Error initializing PayPal button:', err);
        setError('Failed to initialize payment button');
        setIsLoading(false);
        if (onError) onError(err);
      }
    };

    loadPayPalScript();

    // Cleanup
    return () => {
      if (paypalRef.current) {
        paypalRef.current.innerHTML = '';
      }
    };
  }, [planId, billingCycle, onSuccess, onError]);

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-600 text-sm">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-2 text-sm text-red-600 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="paypal-button-container">
      {isLoading && (
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading PayPal...</span>
        </div>
      )}
      <div ref={paypalRef} className={isLoading ? 'hidden' : ''}></div>
    </div>
  );
}
