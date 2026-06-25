/**
 * AI Clause Rewriter Component
 *
 * Rewrite clauses using AI (OpenAI GPT-4 or Anthropic Claude) with multiple modes.
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
import { Textarea } from '../ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import {
  RadioGroup,
  RadioGroupItem
} from '../ui/radio-group';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import {
  AlertCircle,
  CheckCircle2,
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import axios from 'axios';

const ClauseRewriter = ({ clause, onRewriteApplied }) => {
  const [mode, setMode] = useState('reduce_risk');
  const [provider, setProvider] = useState('openai');
  const [numAlternatives, setNumAlternatives] = useState(2);
  const [customInstructions, setCustomInstructions] = useState('');
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState(null);
  const [selectedAlternative, setSelectedAlternative] = useState(0);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [expandedIndex, setExpandedIndex] = useState(0);
  const [error, setError] = useState(null);

  const modes = [
    { value: 'reduce_risk', label: 'Reduce Risk', description: 'Add limitations, caps, and protections' },
    { value: 'simplify', label: 'Simplify', description: 'Convert legalese to plain language' },
    { value: 'favor_client', label: 'Favor Client', description: 'Strengthen client protections' },
    { value: 'favor_vendor', label: 'Favor Vendor', description: 'Protect vendor interests' },
    { value: 'counter_proposal', label: 'Counter-Proposal', description: 'Generate negotiation alternative' }
  ];

  const handleRewrite = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(
        `/api/clauses/${clause.id}/rewrite`,
        {
          mode,
          provider,
          num_alternatives: numAlternatives,
          custom_instructions: customInstructions || undefined
        }
      );

      if (response.data.success) {
        setResult(response.data);
        setSelectedAlternative(0);
        setExpandedIndex(0);
      } else {
        setError(response.data.error || 'Rewrite failed');
      }
    } catch (err) {
      console.error('Error rewriting clause:', err);
      setError(err.response?.data?.error || 'Rewrite failed');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!result || !result.alternatives[selectedAlternative]) {
      setError('No alternative selected');
      return;
    }

    setApplying(true);
    setError(null);

    try {
      const alternative = result.alternatives[selectedAlternative];
      const response = await axios.post(
        `/api/clauses/${clause.id}/apply-rewrite`,
        {
          new_text: alternative.text,
          rewrite_reason: `AI rewrite (${mode})`,
          original_text: result.original_text
        }
      );

      if (response.data.success) {
        // Notify parent
        if (onRewriteApplied) {
          onRewriteApplied({
            ...response.data,
            new_text: alternative.text
          });
        }

        // Show success
        alert('Clause rewritten successfully!');
        setResult(null);
      } else {
        setError(response.data.error || 'Failed to apply rewrite');
      }
    } catch (err) {
      console.error('Error applying rewrite:', err);
      setError(err.response?.data?.error || 'Failed to apply rewrite');
    } finally {
      setApplying(false);
    }
  };

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const getQualityColor = (score) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-orange-600';
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            AI Clause Rewriter
          </CardTitle>
          <CardDescription>
            Rewrite clauses using AI to reduce risk, simplify, or favor specific parties
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Original Clause */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Original Clause
            </label>
            <div className="bg-gray-50 p-3 rounded-lg text-sm">
              {clause.extracted_text || clause.context_sentences || 'No text available'}
            </div>
          </div>

          {/* Rewrite Mode */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Rewrite Mode
            </label>
            <RadioGroup value={mode} onValueChange={setMode}>
              {modes.map((m) => (
                <div key={m.value} className="flex items-start space-x-2 mb-2">
                  <RadioGroupItem value={m.value} id={m.value} />
                  <Label htmlFor={m.value} className="cursor-pointer">
                    <div className="font-medium">{m.label}</div>
                    <div className="text-xs text-gray-500">{m.description}</div>
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>

          {/* Provider & Alternatives */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                AI Provider
              </label>
              <Select value={provider} onValueChange={setProvider}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI GPT-4</SelectItem>
                  <SelectItem value="anthropic">Anthropic Claude</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Number of Alternatives
              </label>
              <Select value={numAlternatives.toString()} onValueChange={(v) => setNumAlternatives(parseInt(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 alternative</SelectItem>
                  <SelectItem value="2">2 alternatives</SelectItem>
                  <SelectItem value="3">3 alternatives</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Custom Instructions */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Custom Instructions (Optional)
            </label>
            <Textarea
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              placeholder="e.g., Add a cap of 2x contract value, Make it more specific to construction contracts"
              rows={2}
            />
          </div>

          {/* Actions */}
          <Button
            onClick={handleRewrite}
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Rewriting...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Generate Rewrites
              </>
            )}
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
      {result && result.alternatives && result.alternatives.length > 0 && (
        <div className="space-y-3">
          {result.alternatives.map((alt, index) => (
            <Card
              key={index}
              className={selectedAlternative === index ? 'border-blue-500 border-2' : ''}
            >
              <CardHeader className="cursor-pointer" onClick={() => {
                setExpandedIndex(expandedIndex === index ? -1 : index);
                setSelectedAlternative(index);
              }}>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-base flex items-center gap-2">
                      Alternative #{alt.rank}
                      {index === 0 && (
                        <Badge variant="success">Best</Badge>
                      )}
                      {selectedAlternative === index && (
                        <Badge variant="outline">Selected</Badge>
                      )}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      Quality: <span className={getQualityColor(alt.quality_score)}>
                        {(alt.quality_score * 100).toFixed(0)}%
                      </span>
                      {' | '}
                      Similarity: {(alt.similarity_to_original * 100).toFixed(0)}%
                    </CardDescription>
                  </div>
                  {expandedIndex === index ? (
                    <ChevronUp className="h-5 w-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-gray-400" />
                  )}
                </div>
              </CardHeader>

              {expandedIndex === index && (
                <CardContent className="space-y-3">
                  {/* Rewritten Text */}
                  <div>
                    <div className="bg-blue-50 p-4 rounded-lg text-sm">
                      {alt.text}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(alt.text, index)}
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

                  {/* Changes */}
                  {alt.changes && alt.changes.length > 0 && (
                    <div>
                      <div className="text-sm font-medium mb-2">Key Changes:</div>
                      <ul className="list-disc list-inside text-sm space-y-1">
                        {alt.changes.map((change, i) => (
                          <li key={i} className="text-gray-700">{change}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Apply Button */}
                  <Button
                    onClick={handleApply}
                    disabled={applying}
                    className="w-full"
                    variant={selectedAlternative === index ? 'default' : 'outline'}
                  >
                    {applying ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Applying...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="h-4 w-4 mr-2" />
                        Apply This Rewrite
                      </>
                    )}
                  </Button>
                </CardContent>
              )}
            </Card>
          ))}

          {/* Fallback Notice */}
          {result.using_fallback && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                AI API not available. Using template-based rewriting as fallback.
                Add OPENAI_API_KEY or ANTHROPIC_API_KEY to .env for AI-powered rewrites.
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}
    </div>
  );
};

export default ClauseRewriter;
