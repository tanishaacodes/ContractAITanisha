import { useState, useEffect } from 'react';
import axios from 'axios';
import { Receipt, Download, CheckCircle, XCircle, Clock, CreditCard } from 'lucide-react';
import useThemeStore from '../../store/themeStore';
import { config } from '../../config/api.config';

/**
 * Payment History Component
 * Displays user's payment transaction history
 */
export default function PaymentHistory() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { theme } = useThemeStore();

  useEffect(() => {
    fetchPaymentHistory();
  }, []);

  const fetchPaymentHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        config.PAYMENT_HISTORY_URL,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      setTransactions(response.data.transactions || []);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching payment history:', err);
      setError(err.response?.data?.error || 'Failed to load payment history');
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'FAILED':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'PENDING':
      case 'PROCESSING':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      default:
        return <Receipt className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      COMPLETED: 'bg-green-500/10 text-green-500',
      FAILED: 'bg-red-500/10 text-red-500',
      PENDING: 'bg-yellow-500/10 text-yellow-500',
      PROCESSING: 'bg-blue-500/10 text-blue-500',
      REFUNDED: `${theme.colors.surface} ${theme.colors.textSecondary}`,
      CANCELLED: `${theme.colors.surface} ${theme.colors.textSecondary}`,
    };

    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${badges[status] || `${theme.colors.surface} ${theme.colors.textSecondary}`}`}>
        {status}
      </span>
    );
  };

  const getPaymentMethodIcon = (method) => {
    if (method === 'PAYPAL') {
      return (
        <div className="flex items-center">
          <div className={`w-8 h-8 ${theme.colors.primarySolid} rounded flex items-center justify-center`}>
            <span className="text-white font-bold text-xs">PP</span>
          </div>
          <span className={`ml-2 text-sm ${theme.colors.textSecondary}`}>PayPal</span>
        </div>
      );
    }
    return (
      <div className="flex items-center">
        <CreditCard className={`w-6 h-6 ${theme.colors.primaryText}`} />
        <span className={`ml-2 text-sm ${theme.colors.textSecondary}`}>Card</span>
      </div>
    );
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className={`animate-spin rounded-full h-10 w-10 border-b-2 ${theme.colors.primaryBorder}`}></div>
        <span className={`ml-3 ${theme.colors.textSecondary}`}>Loading payment history...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${theme.colors.surface} border ${theme.colors.dangerBorder} rounded-lg p-6 text-center ${theme.colors.shadow}`}>
        <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className={`${theme.colors.dangerText} mb-4`}>{error}</p>
        <button
          onClick={fetchPaymentHistory}
          className={`${theme.colors.danger} text-white px-6 py-2 rounded-lg hover:opacity-90 transition`}
        >
          Retry
        </button>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className={`${theme.colors.surface} rounded-lg ${theme.colors.shadow} p-8 text-center`}>
        <Receipt className={`w-16 h-16 ${theme.colors.textTertiary} mx-auto mb-4`} />
        <h3 className={`text-lg font-semibold ${theme.colors.textPrimary} mb-2`}>No Payment History</h3>
        <p className={`${theme.colors.textSecondary} mb-4`}>
          You haven't made any payments yet.
        </p>
        <a
          href="/subscription"
          className={`inline-block ${theme.colors.primarySolid} text-white px-6 py-2 rounded-lg hover:${theme.colors.primaryHover} transition`}
        >
          View Plans
        </a>
      </div>
    );
  }

  return (
    <div className="payment-history">
      {/* Header */}
      <div className="mb-6">
        <h2 className={`text-2xl font-bold ${theme.colors.textPrimary}`}>Payment History</h2>
        <p className={`${theme.colors.textSecondary} mt-1`}>View all your past transactions</p>
      </div>

      {/* Transactions List */}
      <div className={`${theme.colors.surface} rounded-lg ${theme.colors.shadow} overflow-hidden`}>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200/10">
            <thead className={`${theme.colors.surfaceHover}`}>
              <tr>
                <th className={`px-6 py-3 text-left text-xs font-medium ${theme.colors.textSecondary} uppercase tracking-wider`}>
                  Date
                </th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${theme.colors.textSecondary} uppercase tracking-wider`}>
                  Description
                </th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${theme.colors.textSecondary} uppercase tracking-wider`}>
                  Method
                </th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${theme.colors.textSecondary} uppercase tracking-wider`}>
                  Amount
                </th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${theme.colors.textSecondary} uppercase tracking-wider`}>
                  Status
                </th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${theme.colors.textSecondary} uppercase tracking-wider`}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className={`${theme.colors.surface} divide-y divide-gray-200/10`}>
              {transactions.map((transaction) => (
                <tr key={transaction.id} className={`hover:${theme.colors.surfaceHover} transition-colors`}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-sm ${theme.colors.textPrimary}`}>{formatDate(transaction.created_at)}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className={`text-sm font-medium ${theme.colors.textPrimary}`}>
                      {transaction.plan.name}
                    </div>
                    <div className={`text-sm ${theme.colors.textSecondary}`}>{transaction.description}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getPaymentMethodIcon(transaction.payment_method)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-sm font-semibold ${theme.colors.textPrimary}`}>
                      ${transaction.amount} {transaction.currency}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(transaction.status)}
                      <span className="ml-2">{getStatusBadge(transaction.status)}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {transaction.status === 'COMPLETED' && (
                      <button className={`${theme.colors.primaryText} hover:opacity-80 flex items-center transition`}>
                        <Download className="w-4 h-4 mr-1" />
                        Receipt
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
        <div className={`${theme.colors.surface} rounded-lg ${theme.colors.shadow} p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.colors.textSecondary}`}>Total Paid</p>
              <p className={`text-2xl font-bold ${theme.colors.textPrimary}`}>
                ${transactions
                  .filter(t => t.status === 'COMPLETED')
                  .reduce((sum, t) => sum + parseFloat(t.amount), 0)
                  .toFixed(2)}
              </p>
            </div>
            <CheckCircle className="w-12 h-12 text-green-500" />
          </div>
        </div>

        <div className={`${theme.colors.surface} rounded-lg ${theme.colors.shadow} p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.colors.textSecondary}`}>Total Transactions</p>
              <p className={`text-2xl font-bold ${theme.colors.textPrimary}`}>{transactions.length}</p>
            </div>
            <Receipt className={`w-12 h-12 ${theme.colors.primaryText}`} />
          </div>
        </div>

        <div className={`${theme.colors.surface} rounded-lg ${theme.colors.shadow} p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.colors.textSecondary}`}>Successful</p>
              <p className={`text-2xl font-bold ${theme.colors.textPrimary}`}>
                {transactions.filter(t => t.status === 'COMPLETED').length}
              </p>
            </div>
            <CheckCircle className="w-12 h-12 text-green-500" />
          </div>
        </div>
      </div>
    </div>
  );
}
