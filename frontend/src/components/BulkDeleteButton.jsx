import { useState } from 'react';
import { Trash2, AlertTriangle } from 'lucide-react';
import axios from 'axios';

const BulkDeleteButton = ({ selectedContracts, onDeleteComplete }) => {
  const [showConfirm, setShowConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (selectedContracts.length === 0) {
      alert('Please select contracts to delete');
      return;
    }

    setDeleting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/contracts/bulk-delete`,
        { contract_ids: selectedContracts },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      alert(`Successfully deleted ${response.data.deleted_count} contracts!`);
      setShowConfirm(false);
      onDeleteComplete();
    } catch (error) {
      console.error('Error deleting contracts:', error);
      alert('Failed to delete contracts: ' + (error.response?.data?.error || error.message));
    } finally {
      setDeleting(false);
    }
  };

  if (selectedContracts.length === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-8 right-8 z-50">
      {!showConfirm ? (
        <button
          onClick={() => setShowConfirm(true)}
          className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg shadow-lg transition-all transform hover:scale-105"
        >
          <Trash2 className="w-5 h-5" />
          Delete {selectedContracts.length} Contract{selectedContracts.length > 1 ? 's' : ''}
        </button>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl p-6 max-w-md">
          <div className="flex items-start gap-3 mb-4">
            <AlertTriangle className="w-6 h-6 text-red-500 flex-shrink-0" />
            <div>
              <h3 className="font-bold text-lg text-gray-900 dark:text-white">
                Confirm Deletion
              </h3>
              <p className="text-gray-600 dark:text-gray-300 text-sm mt-1">
                Are you sure you want to delete {selectedContracts.length} contract{selectedContracts.length > 1 ? 's' : ''}?
                This action cannot be undone.
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setShowConfirm(false)}
              disabled={deleting}
              className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default BulkDeleteButton;
