/**
 * BOQ Table Component
 * Displays Bill of Quantities with category breakdown
 */
import React, { useState, useMemo } from 'react';
import tenderService from '../../services/tenderService';

const BOQTable = ({ workItems = [], tenderId, onReanalyzed }) => {
  const [reanalyzing, setReanalyzing] = useState(false);
  const [reanalyzeError, setReanalyzeError] = useState(null);

  const handleReanalyze = async () => {
    if (!tenderId) return;
    setReanalyzing(true);
    setReanalyzeError(null);
    try {
      const updated = await tenderService.reanalyze(tenderId);
      if (onReanalyzed) onReanalyzed(updated);
    } catch (err) {
      setReanalyzeError(err.response?.data?.error || 'Re-analysis failed. Please try again.');
    } finally {
      setReanalyzing(false);
    }
  };
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  // Calculate category breakdown
  const categoryStats = useMemo(() => {
    const stats = {
      CIVIL: { count: 0, value: 0 },
      MECHANICAL: { count: 0, value: 0 },
      MEP: { count: 0, value: 0 },
      OTHER: { count: 0, value: 0 },
    };

    workItems.forEach((item) => {
      const category = item.category || 'OTHER';
      if (stats[category]) {
        stats[category].count += 1;
        stats[category].value += parseFloat(item.estimated_cost || 0);
      }
    });

    return stats;
  }, [workItems]);

  // Filter items
  const filteredItems = useMemo(() => {
    return workItems.filter((item) => {
      const matchesCategory = selectedCategory === 'ALL' || item.category === selectedCategory;
      const matchesSearch = !searchTerm ||
        item.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.item_code?.toLowerCase().includes(searchTerm.toLowerCase());

      return matchesCategory && matchesSearch;
    });
  }, [workItems, selectedCategory, searchTerm]);

  // Calculate totals
  const totalValue = useMemo(() => {
    return filteredItems.reduce((sum, item) => sum + parseFloat(item.estimated_cost || 0), 0);
  }, [filteredItems]);

  const formatCurrency = (value) => {
    return `₹${(value / 100000).toFixed(2)} L`;
  };

  const getCategoryColor = (category) => {
    const colors = {
      CIVIL: 'bg-blue-100 text-blue-800',
      MECHANICAL: 'bg-purple-100 text-purple-800',
      MEP: 'bg-green-100 text-green-800',
      OTHER: 'bg-slate-800 text-white',
    };
    return colors[category] || colors.OTHER;
  };

  const totalEstimatedValue = Object.values(categoryStats).reduce((sum, cat) => sum + cat.value, 0);

  return (
    <div className="space-y-6">
      {/* Work Breakdown Summary Table */}
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 overflow-hidden">
        <div className="bg-slate-900 px-6 py-4 border-b border-slate-700">
          <h3 className="text-lg font-bold text-white flex items-center">
            <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Work Breakdown Summary
          </h3>
        </div>
        <table className="min-w-full">
          <thead className="bg-slate-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Category</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Items</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Total Value</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">% of Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {Object.entries(categoryStats).map(([category, stats]) => {
              const percentage = totalEstimatedValue > 0 ? (stats.value / totalEstimatedValue * 100) : 0;
              return (
                <tr key={category} className="hover:bg-slate-900">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getCategoryColor(category)}`}>
                      {category}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white font-medium">
                    {stats.count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white font-medium">
                    {formatCurrency(stats.value)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end">
                      <div className="w-24 bg-slate-700 rounded-full h-2 mr-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-slate-300">{percentage.toFixed(1)}%</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot className="bg-slate-900">
            <tr className="border-t-2 border-blue-600">
              <td className="px-6 py-4 text-sm font-bold text-white">TOTAL</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-bold text-white">
                {workItems.length}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-bold text-white">
                {formatCurrency(totalEstimatedValue)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-bold text-white">
                100%
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Category Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {Object.entries(categoryStats).map(([category, stats]) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`text-left p-4 rounded-lg border-2 transition-all ${
              selectedCategory === category
                ? 'border-blue-600 bg-blue-900/30'
                : 'border-slate-700 bg-slate-800 hover:border-slate-600'
            }`}
          >
            <div className="text-sm font-medium text-slate-400 mb-1">
              {category}
            </div>
            <div className="text-2xl font-bold text-white mb-2">
              {stats.count}
            </div>
            <div className="text-sm text-slate-300">
              {formatCurrency(stats.value)}
            </div>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setSelectedCategory('ALL')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === 'ALL'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-200 hover:bg-slate-700'
              }`}
            >
              All Items ({workItems.length})
            </button>
            {Object.keys(categoryStats).map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedCategory === category
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-200 hover:bg-slate-700'
                }`}
              >
                {category} ({categoryStats[category].count})
              </button>
            ))}
          </div>

          <div className="relative">
            <input
              type="text"
              placeholder="Search BOQ items..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <svg
              className="absolute left-3 top-2.5 w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* BOQ Table */}
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-slate-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Item Code
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Quantity
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Unit
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Estimated Cost
                </th>
              </tr>
            </thead>
            <tbody className="bg-slate-800 divide-y divide-gray-200">
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center">
                    <div className="text-slate-400 mb-4">No BOQ items found in this tender document.</div>
                    {tenderId && (
                      <div>
                        <p className="text-slate-500 text-sm mb-3">
                          If this tender contains scope or criteria items, click Re-analyze to extract them.
                        </p>
                        {reanalyzeError && (
                          <p className="text-red-400 text-sm mb-3">{reanalyzeError}</p>
                        )}
                        <button
                          onClick={handleReanalyze}
                          disabled={reanalyzing}
                          className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded-lg disabled:opacity-50 flex items-center mx-auto"
                        >
                          {reanalyzing ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              Re-analyzing...
                            </>
                          ) : (
                            <>
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                              </svg>
                              Re-analyze Document
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ) : (
                filteredItems.map((item, index) => (
                  <tr key={index} className="hover:bg-slate-900">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                      {item.item_code || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-200">
                      {item.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getCategoryColor(item.category)}`}>
                        {item.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">
                      {item.quantity ? parseFloat(item.quantity).toLocaleString() : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-slate-200">
                      {item.unit || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-white">
                      {item.estimated_cost ? formatCurrency(item.estimated_cost) : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            {filteredItems.length > 0 && (
              <tfoot className="bg-slate-900">
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-sm font-bold text-white text-right">
                    Total:
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-white text-right">
                    {formatCurrency(totalValue)}
                  </td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </div>

      {/* Export Button */}
      <div className="flex justify-end">
        <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export to Excel
        </button>
      </div>
    </div>
  );
};

export default BOQTable;
