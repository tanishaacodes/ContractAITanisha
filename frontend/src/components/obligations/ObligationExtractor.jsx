/**
 * Obligation Extraction Component
 *
 * Extracts obligations from contract clauses using AI/regex patterns.
 * Displays obligations in a filterable, sortable table.
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Checkbox } from '../ui/checkbox';
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';
import axios from 'axios';

const ObligationExtractor = ({ contractId }) => {
  const [obligations, setObligations] = useState([]);
  const [filteredObligations, setFilteredObligations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState(null);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [partyFilter, setPartyFilter] = useState('ALL');
  const [completedFilter, setCompletedFilter] = useState('ALL');

  // Stats
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    pending: 0,
    highPriority: 0
  });

  useEffect(() => {
    if (contractId) {
      fetchObligations();
    }
  }, [contractId]);

  useEffect(() => {
    applyFilters();
  }, [obligations, categoryFilter, priorityFilter, partyFilter, completedFilter]);

  const fetchObligations = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `/api/contracts/${contractId}/obligations/list`
      );

      if (response.data.success) {
        setObligations(response.data.obligations);
        calculateStats(response.data.obligations);
      } else {
        setError(response.data.error || 'Failed to fetch obligations');
      }
    } catch (err) {
      console.error('Error fetching obligations:', err);
      setError(err.response?.data?.error || 'Failed to fetch obligations');
    } finally {
      setLoading(false);
    }
  };

  const extractObligations = async (reextract = false) => {
    setExtracting(true);
    setError(null);

    try {
      const response = await axios.post(
        `/api/contracts/${contractId}/obligations/extract`,
        { reextract }
      );

      if (response.data.success) {
        // Refresh obligations list
        await fetchObligations();
      } else {
        setError(response.data.error || 'Extraction failed');
      }
    } catch (err) {
      console.error('Error extracting obligations:', err);
      setError(err.response?.data?.error || 'Extraction failed');
    } finally {
      setExtracting(false);
    }
  };

  const markAsComplete = async (obligationId) => {
    try {
      const response = await axios.put(
        `/api/obligations/${obligationId}/complete`,
        {
          completion_notes: 'Marked as complete from UI'
        }
      );

      if (response.data.success) {
        // Update local state
        setObligations(prev =>
          prev.map(obl =>
            obl.id === obligationId
              ? { ...obl, is_completed: true, completed_at: new Date().toISOString() }
              : obl
          )
        );
      }
    } catch (err) {
      console.error('Error marking obligation as complete:', err);
    }
  };

  const applyFilters = () => {
    let filtered = [...obligations];

    if (categoryFilter !== 'ALL') {
      filtered = filtered.filter(obl => obl.category === categoryFilter);
    }

    if (priorityFilter !== 'ALL') {
      filtered = filtered.filter(obl => obl.priority === priorityFilter);
    }

    if (partyFilter !== 'ALL') {
      filtered = filtered.filter(obl => obl.responsible_party === partyFilter);
    }

    if (completedFilter !== 'ALL') {
      const isCompleted = completedFilter === 'COMPLETED';
      filtered = filtered.filter(obl => obl.is_completed === isCompleted);
    }

    setFilteredObligations(filtered);
  };

  const calculateStats = (obligationsList) => {
    const stats = {
      total: obligationsList.length,
      completed: obligationsList.filter(o => o.is_completed).length,
      pending: obligationsList.filter(o => !o.is_completed).length,
      highPriority: obligationsList.filter(o => o.priority === 'HIGH').length
    };
    setStats(stats);
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'HIGH': return 'destructive';
      case 'MEDIUM': return 'warning';
      case 'LOW': return 'secondary';
      default: return 'default';
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      PAYMENT: 'bg-green-100 text-green-800',
      DELIVERY: 'bg-blue-100 text-blue-800',
      COMPLIANCE: 'bg-purple-100 text-purple-800',
      REPORTING: 'bg-yellow-100 text-yellow-800',
      NOTICE: 'bg-orange-100 text-orange-800',
      TERMINATION: 'bg-red-100 text-red-800',
      OTHER: 'bg-gray-100 text-gray-800'
    };
    return colors[category] || colors.OTHER;
  };

  const exportToCSV = () => {
    const headers = ['Title', 'Category', 'Priority', 'Responsible Party', 'Due Date', 'Status'];
    const rows = filteredObligations.map(obl => [
      obl.title,
      obl.category,
      obl.priority,
      obl.responsible_party,
      obl.due_date_text || 'Not specified',
      obl.is_completed ? 'Completed' : 'Pending'
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `obligations-${contractId}.csv`;
    a.click();
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <RefreshCw className="h-6 w-6 animate-spin mr-2" />
            <span>Loading obligations...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Stats */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Contract Obligations</CardTitle>
            <div className="flex gap-2">
              <Button
                onClick={() => extractObligations(obligations.length > 0)}
                disabled={extracting}
                variant="outline"
              >
                {extracting ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                    Extracting...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    {obligations.length > 0 ? 'Re-extract' : 'Extract'}
                  </>
                )}
              </Button>
              {filteredObligations.length > 0 && (
                <Button onClick={exportToCSV} variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Export CSV
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Total Obligations</div>
              <div className="text-2xl font-bold">{stats.total}</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Completed</div>
              <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Pending</div>
              <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">High Priority</div>
              <div className="text-2xl font-bold text-red-600">{stats.highPriority}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center text-red-800">
              <AlertCircle className="h-5 w-5 mr-2" />
              {error}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      {obligations.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <Filter className="h-5 w-5 text-gray-500" />
              <div className="grid grid-cols-4 gap-4 flex-1">
                <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Categories</SelectItem>
                    <SelectItem value="PAYMENT">Payment</SelectItem>
                    <SelectItem value="DELIVERY">Delivery</SelectItem>
                    <SelectItem value="COMPLIANCE">Compliance</SelectItem>
                    <SelectItem value="REPORTING">Reporting</SelectItem>
                    <SelectItem value="NOTICE">Notice</SelectItem>
                    <SelectItem value="TERMINATION">Termination</SelectItem>
                    <SelectItem value="OTHER">Other</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Priority" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Priorities</SelectItem>
                    <SelectItem value="HIGH">High</SelectItem>
                    <SelectItem value="MEDIUM">Medium</SelectItem>
                    <SelectItem value="LOW">Low</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={partyFilter} onValueChange={setPartyFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Party" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Parties</SelectItem>
                    <SelectItem value="YOUR_COMPANY">Your Company</SelectItem>
                    <SelectItem value="COUNTERPARTY">Counterparty</SelectItem>
                    <SelectItem value="BOTH">Both Parties</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={completedFilter} onValueChange={setCompletedFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Status</SelectItem>
                    <SelectItem value="PENDING">Pending</SelectItem>
                    <SelectItem value="COMPLETED">Completed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Obligations Table */}
      {obligations.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-gray-500">
            <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p>No obligations found. Click "Extract" to analyze the contract.</p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12"></TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Responsible Party</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredObligations.map((obligation) => (
                  <TableRow key={obligation.id}>
                    <TableCell>
                      {obligation.is_completed ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      ) : (
                        <Clock className="h-5 w-5 text-yellow-500" />
                      )}
                    </TableCell>
                    <TableCell className="font-medium">
                      {obligation.title}
                    </TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded text-xs ${getCategoryColor(obligation.category)}`}>
                        {obligation.category}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getPriorityColor(obligation.priority)}>
                        {obligation.priority}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {obligation.responsible_party.replace('_', ' ')}
                    </TableCell>
                    <TableCell className="text-sm">
                      {obligation.due_date_text || <span className="text-gray-400">Not specified</span>}
                    </TableCell>
                    <TableCell>
                      {obligation.is_completed ? (
                        <Badge variant="success">Completed</Badge>
                      ) : (
                        <Badge variant="secondary">Pending</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {!obligation.is_completed && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => markAsComplete(obligation.id)}
                        >
                          Mark Complete
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {filteredObligations.length === 0 && (
              <div className="p-8 text-center text-gray-500">
                No obligations match the selected filters.
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ObligationExtractor;
