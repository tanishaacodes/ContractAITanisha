/**
 * Clause Addition Component
 *
 * Add new clauses to contracts with automatic risk assessment and what-if simulation.
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Alert, AlertDescription } from '../ui/alert';
import {
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  Plus,
  Eye
} from 'lucide-react';
import axios from 'axios';

const ClauseAddition = ({ contractId, onClauseAdded }) => {
  const [clauseName, setClauseName] = useState('');
  const [clauseType, setClauseType] = useState('general');
  const [clauseText, setClauseText] = useState('');
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [result, setResult] = useState(null);
  const [simulationResult, setSimulationResult] = useState(null);
  const [error, setError] = useState(null);

  const clauseTypes = [
    { value: 'indemnity', label: 'Indemnity' },
    { value: 'liability', label: 'Liability' },
    { value: 'termination', label: 'Termination' },
    { value: 'payment', label: 'Payment' },
    { value: 'warranty', label: 'Warranty' },
    { value: 'confidentiality', label: 'Confidentiality' },
    { value: 'intellectual_property', label: 'Intellectual Property' },
    { value: 'force_majeure', label: 'Force Majeure' },
    { value: 'dispute_resolution', label: 'Dispute Resolution' },
    { value: 'general', label: 'General' }
  ];

  const handleSimulate = async () => {
    if (!clauseName || !clauseText || clauseText.length < 10) {
      setError('Please provide clause name and text (minimum 10 characters)');
      return;
    }

    setSimulating(true);
    setError(null);
    setSimulationResult(null);

    try {
      const response = await axios.post(
        `/api/contracts/${contractId}/clauses/simulate-addition`,
        {
          clause_name: clauseName,
          clause_type: clauseType,
          clause_text: clauseText
        }
      );

      if (response.data.success) {
        setSimulationResult(response.data);
      } else {
        setError(response.data.error || 'Simulation failed');
      }
    } catch (err) {
      console.error('Error simulating clause addition:', err);
      setError(err.response?.data?.error || 'Simulation failed');
    } finally {
      setSimulating(false);
    }
  };

  const handleAdd = async (runSimulation = true) => {
    if (!clauseName || !clauseText || clauseText.length < 10) {
      setError('Please provide clause name and text (minimum 10 characters)');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(
        `/api/contracts/${contractId}/clauses/add`,
        {
          clause_name: clauseName,
          clause_type: clauseType,
          clause_text: clauseText,
          run_simulation: runSimulation
        }
      );

      if (response.data.success) {
        setResult(response.data);

        // Clear form
        setClauseName('');
        setClauseText('');
        setClauseType('general');
        setSimulationResult(null);

        // Notify parent
        if (onClauseAdded) {
          onClauseAdded(response.data);
        }
      } else {
        setError(response.data.error || 'Failed to add clause');
      }
    } catch (err) {
      console.error('Error adding clause:', err);
      setError(err.response?.data?.error || 'Failed to add clause');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'HIGH': return 'destructive';
      case 'MEDIUM': return 'warning';
      case 'LOW': return 'success';
      default: return 'secondary';
    }
  };

  const formatCurrency = (amount) => {
    if (amount >= 10000000) {
      return `₹${(amount / 10000000).toFixed(1)} Cr`;
    } else if (amount >= 100000) {
      return `₹${(amount / 100000).toFixed(1)} L`;
    }
    return `₹${amount.toLocaleString()}`;
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Add New Clause</CardTitle>
          <CardDescription>
            Add a custom clause with automatic risk assessment and exposure impact analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Clause Name */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Clause Name *
            </label>
            <Input
              value={clauseName}
              onChange={(e) => setClauseName(e.target.value)}
              placeholder="e.g., Force Majeure, Payment Terms"
              disabled={loading}
            />
          </div>

          {/* Clause Type */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Clause Type
            </label>
            <Select value={clauseType} onValueChange={setClauseType} disabled={loading}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {clauseTypes.map(type => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Clause Text */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Clause Text *
            </label>
            <Textarea
              value={clauseText}
              onChange={(e) => setClauseText(e.target.value)}
              placeholder="Enter the full clause text..."
              rows={6}
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">
              {clauseText.length} characters (minimum 10 required)
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button
              onClick={handleSimulate}
              disabled={simulating || loading || !clauseName || !clauseText}
              variant="outline"
            >
              <Eye className="h-4 w-4 mr-2" />
              {simulating ? 'Simulating...' : 'Preview Impact'}
            </Button>
            <Button
              onClick={() => handleAdd(true)}
              disabled={loading || simulating || !clauseName || !clauseText}
            >
              <Plus className="h-4 w-4 mr-2" />
              {loading ? 'Adding...' : 'Add Clause'}
            </Button>
          </div>

          {/* Error */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Simulation Results */}
      {simulationResult && (
        <Card>
          <CardHeader>
            <CardTitle>Impact Preview</CardTitle>
            <CardDescription>
              What-if analysis shows the impact of adding this clause
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Risk Assessment */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-3">Risk Assessment</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-600">Risk Score</div>
                  <div className="text-2xl font-bold">
                    {(simulationResult.risk_assessment.risk_score * 100).toFixed(0)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Risk Level</div>
                  <div className="mt-1">
                    <Badge variant={getRiskColor(simulationResult.risk_assessment.risk_level)}>
                      {simulationResult.risk_assessment.risk_level}
                    </Badge>
                  </div>
                </div>
              </div>

              {simulationResult.risk_assessment.risk_factors?.keywords_found?.length > 0 && (
                <div className="mt-3">
                  <div className="text-sm text-gray-600 mb-2">Risk Factors Detected:</div>
                  <div className="flex flex-wrap gap-1">
                    {simulationResult.risk_assessment.risk_factors.keywords_found.map((keyword, idx) => (
                      <span key={idx} className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded">
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Exposure Impact */}
            {simulationResult.impact_analysis?.success && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold mb-3">Financial Exposure Impact</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm text-gray-600">Current</div>
                    <div className="text-xl font-bold">
                      {formatCurrency(simulationResult.impact_analysis.current_exposure)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">After Addition</div>
                    <div className="text-xl font-bold">
                      {formatCurrency(simulationResult.impact_analysis.new_exposure)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Increase</div>
                    <div className="flex items-center gap-1">
                      <TrendingUp className="h-5 w-5 text-red-500" />
                      <div className="text-xl font-bold text-red-600">
                        {formatCurrency(simulationResult.impact_analysis.exposure_delta)}
                      </div>
                    </div>
                    <div className="text-xs text-gray-600">
                      +{simulationResult.impact_analysis.risk_increase_pct.toFixed(1)}%
                    </div>
                  </div>
                </div>

                {simulationResult.impact_analysis.recommendation && (
                  <Alert className="mt-3">
                    <AlertDescription>
                      {simulationResult.impact_analysis.recommendation}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Success Result */}
      {result && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="text-green-800 flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5" />
              Clause Added Successfully
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-600">Clause ID</div>
                <div className="font-mono text-xs">{result.clause_id}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Risk Assessment</div>
                <Badge variant={getRiskColor(result.risk_level)}>
                  {result.risk_level} ({(result.risk_score * 100).toFixed(0)}%)
                </Badge>
              </div>
            </div>

            {result.simulation?.success && (
              <div className="border-t pt-3">
                <div className="text-sm font-medium mb-2">Exposure Impact:</div>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">Before:</span>{' '}
                    <span className="font-semibold">
                      {formatCurrency(result.simulation.current_exposure)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">After:</span>{' '}
                    <span className="font-semibold">
                      {formatCurrency(result.simulation.new_exposure)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Increase:</span>{' '}
                    <span className="font-semibold text-red-600">
                      +{result.simulation.risk_increase_pct.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ClauseAddition;
