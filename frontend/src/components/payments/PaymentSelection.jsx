import { useState } from 'react';
import PayPalButton from './PayPalButton';
import StripeCheckout from './StripeCheckout';
import { CreditCard, DollarSign } from 'lucide-react';

/**
 * Payment Selection Component
 * Allows users to choose between PayPal and Stripe (Credit Card) payment methods
 *
 * @param {Object} props
 * @param {Object} props.plan - Pricing plan object
 * @param {string} props.billingCycle - "MONTHLY" or "YEARLY"
 * @param {Function} props.onSuccess - Callback when payment succeeds
 * @param {Function} props.onCancel - Callback when user cancels
 */
export default function PaymentSelection({ plan, billingCycle = 'MONTHLY', onSuccess, onCancel }) {
  const [selectedMethod, setSelectedMethod] = useState('stripe'); // 'stripe' or 'paypal'

  // Calculate total amount
  const priceMonthly = plan.priceMonthly || plan.price_monthly || 0;
  const amount = billingCycle === 'YEARLY'
    ? priceMonthly * 12
    : priceMonthly;

  const handlePaymentSuccess = (data) => {
    console.log('Payment successful:', data);
    if (onSuccess) {
      onSuccess(data);
    } else {
      // Default success behavior
      alert('Payment successful! Your subscription has been activated.');
      window.location.href = '/dashboard';
    }
  };

  const handlePaymentError = (error) => {
    console.error('Payment error:', error);
    // Error is already handled in individual payment components
  };

  return (
    <div className="payment-selection max-w-2xl mx-auto">
      {/* Payment Summary */}
      <div className="bg-[#1e293b] rounded-lg shadow-xl p-6 mb-6 border border-gray-700">
        <h3 className="text-xl font-semibold text-white mb-4">Payment Summary</h3>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-gray-400">Plan:</span>
            <span className="font-medium text-white">{plan.displayName || plan.display_name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Billing Cycle:</span>
            <span className="font-medium text-white">{billingCycle}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Contract Limit:</span>
            <span className="font-medium text-white">
              {(plan.contractLimit ?? plan.contract_limit) === -1 ? 'Unlimited' : (plan.contractLimit ?? plan.contract_limit)} contracts
            </span>
          </div>
          <div className="border-t border-gray-700 pt-3 flex justify-between text-lg">
            <span className="font-semibold text-white">Total:</span>
            <span className="font-bold text-blue-400">${amount.toFixed(2)} USD</span>
          </div>
        </div>
      </div>

      {/* Payment Method Selection */}
      <div className="bg-[#1e293b] rounded-lg shadow-xl p-6 mb-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Select Payment Method</h3>

        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* Stripe/Card Option */}
          <button
            onClick={() => setSelectedMethod('stripe')}
            className={`p-4 border-2 rounded-lg transition-all duration-200 flex flex-col items-center justify-center ${
              selectedMethod === 'stripe'
                ? 'border-blue-500 bg-blue-900/30'
                : 'border-gray-600 hover:border-gray-500 bg-[#0f172a]'
            }`}
          >
            <CreditCard className={`w-8 h-8 mb-2 ${
              selectedMethod === 'stripe' ? 'text-blue-400' : 'text-gray-400'
            }`} />
            <span className={`font-medium ${
              selectedMethod === 'stripe' ? 'text-blue-400' : 'text-gray-300'
            }`}>
              Credit / Debit Card
            </span>
            <span className="text-xs text-gray-500 mt-1">Visa, Mastercard, Amex</span>
          </button>

          {/* PayPal Option */}
          <button
            onClick={() => setSelectedMethod('paypal')}
            className={`p-4 border-2 rounded-lg transition-all duration-200 flex flex-col items-center justify-center ${
              selectedMethod === 'paypal'
                ? 'border-blue-500 bg-blue-900/30'
                : 'border-gray-600 hover:border-gray-500 bg-[#0f172a]'
            }`}
          >
            <DollarSign className={`w-8 h-8 mb-2 ${
              selectedMethod === 'paypal' ? 'text-blue-400' : 'text-gray-400'
            }`} />
            <span className={`font-medium ${
              selectedMethod === 'paypal' ? 'text-blue-400' : 'text-gray-300'
            }`}>
              PayPal
            </span>
            <span className="text-xs text-gray-500 mt-1">PayPal Balance or Card</span>
          </button>
        </div>

        {/* Payment Form Area */}
        <div className="mt-6">
          {selectedMethod === 'stripe' && (
            <div>
              <h4 className="text-md font-medium text-white mb-4">Enter Card Details</h4>
              <StripeCheckout
                planId={plan.id}
                billingCycle={billingCycle}
                onSuccess={handlePaymentSuccess}
                onError={handlePaymentError}
              />
            </div>
          )}

          {selectedMethod === 'paypal' && (
            <div>
              <h4 className="text-md font-medium text-white mb-4">Pay with PayPal</h4>
              <PayPalButton
                planId={plan.id}
                billingCycle={billingCycle}
                onSuccess={handlePaymentSuccess}
                onError={handlePaymentError}
              />
            </div>
          )}
        </div>
      </div>

      {/* Security & Features Info */}
      <div className="bg-[#0f172a] rounded-lg p-4 border border-gray-700">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-green-400 font-semibold mb-1">✓ Secure Payment</div>
            <div className="text-xs text-gray-500">256-bit SSL encryption</div>
          </div>
          <div>
            <div className="text-green-400 font-semibold mb-1">✓ Money Back</div>
            <div className="text-xs text-gray-500">30-day guarantee</div>
          </div>
          <div>
            <div className="text-green-400 font-semibold mb-1">✓ Cancel Anytime</div>
            <div className="text-xs text-gray-500">No commitments</div>
          </div>
        </div>
      </div>

      {/* Cancel Button */}
      {onCancel && (
        <div className="mt-6 text-center">
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-white underline"
          >
            Cancel and go back
          </button>
        </div>
      )}
    </div>
  );
}
