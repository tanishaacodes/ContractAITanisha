/**
 * Custom hook for managing contract selection via URL params
 * Provides consistent contract selection behavior across enterprise pages
 */
import { useSearchParams } from 'react-router-dom';

export function useContractSelector() {
  const [searchParams, setSearchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || '';

  const handleContractSelect = (id) => {
    if (id) {
      setSearchParams({ contractId: id });
    } else {
      setSearchParams({});
    }
  };

  const clearSelection = () => {
    setSearchParams({});
  };

  return {
    contractId,
    handleContractSelect,
    clearSelection,
    hasContract: Boolean(contractId)
  };
}
