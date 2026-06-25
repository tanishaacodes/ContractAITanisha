/**
 * Counter-Proposal Generator Component
 *
 * Generate AI-powered counter-proposals for contract negotiations.
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
  TrendingUp,
  Lightbulb,
  Target,
  Shield,
  Copy,
  Check
} from 'lucide-react';
import axios from 'axios';

const CounterProposalGenerator = ({ clause, counterparties = [] }) => {
  const [concerns, setConcerns] = useState(['']);
  const [position, setPosition] = useState('client');
  const [counterpartyId, setCounterpartyId] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [error, setError] = useState(null);

  const handleAddConcern = () => {
    setConcerns([...concerns, '']);
  };

  const handleRemoveConcern = (index) => {
    setConcerns(concerns.filter((_, i) => i !== index));
  };

  const handleConcernChange = (index, value) => {
    const newConcerns = [...concerns];
    newConcerns[index] = value;
    setConcerns(newConcerns);
  };

  const handleGenerate = async () => {
    const validConcerns = concerns.filter(c => c.trim().length > 0);

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(
        `/api/clauses/${clause.id}/counter-proposal`,
        {
          concerns: validConcerns.length > 0 ? validConcerns : undefined,
          your_position: position,
          counterparty_id: counterpartyId || undefined,
          provider: 'openai'
        }
      );

      if (response.data.success) {
        setResult(response.data);
      } else {
        setError(response.data.error || 'Failed to generate counter-proposal');
      }
    } catch (err) {
      console.error('Error generating counter-proposal:', err);
      setError(err.response?.data?.error || 'Failed to generate counter-proposal');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const getStrategyIcon = (approach) => {
    switch (approach) {
      case 'CONFIDENT': return <Target className="h-5 w-5 text-green-600" />;
      case 'COLLABORATIVE': return <Lightbulb className="h-5 w-5 text-blue-600" />;
      case 'CAUTIOUS': return <Shield className="h-5 w-5 text-yellow-600" />;
      default: return <AlertCircle className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStrategyColor = (approach) => {
    switch (approach) {
      case 'CONFIDENT': return 'success';
      case 'COLLABORATIVE': return 'default';
      case 'CAUTIOUS': return 'warning';
      default: return 'secondary';
    }
  };

  const getAcceptanceColor = (likelihood) => {
    if (likelihood >= 0.7) return 'text-green-600';
    if (likelihood >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5" />
            Counter-Proposal Generator
          </CardTitle>
          <CardDescription>
            Generate AI-powered counter-proposals with negotiation strategy
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Proposed Clause */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Proposed Clause
            </label>
            <div className="bg-gray-50 p-3 rounded-lg text-sm">
              {clause.extracted_text || clause.context_sentences || 'No text available'}
            </div>
          </div>

          {/* Your Position */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Your Position
            </label>
            <Select value={position} onValueChange={setPosition}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="client">Client / Buyer</SelectItem>
                <SelectItem value="vendor">Vendor / Supplier</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Counterparty */}
          {counterparties.length > 0 && (
            <div>
              <label className="block text-sm font-medium mb-2">
                Counterparty (Optional)
              </label>
              <Select value={counterpartyId} onValueChange={setCounterpartyId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select counterparty..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">None</SelectItem>
                  {counterparties.map(cp => (
                    <SelectItem key={cp.id} value={cp.id}>
                      {cp.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Concerns */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium">
                Your Concerns (Optional)
              </label>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleAddConcern}
              >
                + Add Concern
              </Button>
            </div>
            {concerns.map((concern, index) => (
              <div key={index} className="flex gap-2 mb-2">
                <Input
                  value={concern}
                  onChange={(e) => handleConcernChange(index, e.target.value)}
                  placeholder="e.g., Unlimited liability, No termination rights"
                />
                {concerns.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveConcern(index)}
                  >
                    ✕
                  </Button>
                )}
              </div>
            ))}
          </div>

          {/* Generate Button */}
          <Button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full"
          >
            {loading ? 'Generating...' : 'Generate Counter-Proposals'}
          </Button>

          {/* Error */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Negotiation Strategy */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {getStrategyIcon(result.negotiation_strategy.approach)}
                Negotiation Strategy
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-600">Approach</div>
                  <Badge variant={getStrategyColor(result.negotiation_strategy.approach)}>
                    {result.negotiation_strategy.approach}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Acceptance Likelihood</div>
                  <div className={`text-2xl font-bold ${getAcceptanceColor(result.negotiation_strategy.acceptance_likelihood / 100)}`}>
                    {result.negotiation_strategy.acceptance_likelihood}%
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="text-sm font-medium mb-1">Reasoning:</div>
                <div className="text-sm">{result.negotiation_strategy.reasoning}</div>
              </div>

              <div className="bg-green-50 p-3 rounded-lg">
                <div className="text-sm font-medium mb-1">Suggested Action:</div>
                <div className="text-sm">{result.negotiation_strategy.suggested_action}</div>
              </div>

              {result.negotiation_strategy.fallback_positions?.length > 0 && (
                <div>
                  <div className="text-sm font-medium mb-2">Fallback Positions:</div>
                  <ul className="list-disc list-inside text-sm space-y-1">
                    {result.negotiation_strategy.fallback_positions.map((pos, i) => (
                      <li key={i}>{pos}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Counter-Proposals */}
          {result.counter_proposals && result.counter_proposals.map((proposal, index) => (
            <Card key={index} className={index === 0 ? 'border-blue-500' : ''}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-base flex items-center gap-2">
                      Counter-Proposal #{proposal.rank}
                      {index === 0 && <Badge variant="success">Recommended</Badge>}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      Acceptance Likelihood:{' '}
                      <span className={getAcceptanceColor(proposal.acceptance_likelihood)}>
                        {(proposal.acceptance_likelihood * 100).toFixed(0)}%
                      </span>
                    </CardDescription>
                  </div>
                  <TrendingUp
                    className={`h-5 w-5 ${getAcceptanceColor(proposal.acceptance_likelihood)}`}
                  />
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Proposal Text */}
                <div>
                  <div className="text-sm font-medium mb-2">Proposed Language:</div>
                  <div className="bg-blue-50 p-4 rounded-lg text-sm">
                    {proposal.text}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(proposal.text, index)}
                    className="mt-2"
                  >
                    {copiedIndex === index ? (
                      <>
                        <Check className="h-4 w-4 mr-2" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4 mr-2" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>

                {/* Rationale */}
                {proposal.rationale && (
                  <div>
                    <div className="text-sm font-medium mb-2">Rationale:</div>
                    <div className="bg-gray-50 p-3 rounded-lg text-sm">
                      {proposal.rationale}
                    </div>
                  </div>
                )}

                {/* Compromises */}
                {proposal.compromises && proposal.compromises.length > 0 && (
                  <div>
                    <div className="text-sm font-medium mb-2">Alternative Compromises:</div>
                    <ul className="list-disc list-inside text-sm space-y-1">
                      {proposal.compromises.map((comp, i) => (
                        <li key={i}>{comp}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Changes */}
                {proposal.changes && proposal.changes.length > 0 && (
                  <div>
                    <div className="text-sm font-medium mb-2">Key Changes:</div>
                    <div className="flex flex-wrap gap-2">
                      {proposal.changes.map((change, i) => (
                        <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                          {change}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default CounterProposalGenerator;
