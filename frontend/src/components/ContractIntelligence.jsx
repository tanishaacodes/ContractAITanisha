import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Loader2, Brain, AlertCircle, CheckCircle } from 'lucide-react';
import useThemeStore from '../store/themeStore';
import { config } from '../config/api.config';

const API_BASE_URL = config.API_BASE_URL;

const ContractIntelligence = ({ contractId }) => {
  const { theme } = useThemeStore();
  const [intelligence, setIntelligence] = useState(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (contractId) {
      fetchIntelligence();
    }
  }, [contractId]);

  const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  const fetchIntelligence = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `${API_BASE_URL}/alfresco/contracts/${contractId}/intelligence`,
        { headers: getAuthHeader() }
      );

      if (response.data.status === 'success') {
        setIntelligence(response.data.intelligence);
      } else {
        setIntelligence(null);
      }
    } catch (err) {
      if (err.response?.status === 404) {
        setIntelligence(null);
      } else {
        setError(err.response?.data?.message || 'Failed to fetch intelligence');
      }
    } finally {
      setLoading(false);
    }
  };

  const extractIntelligence = async () => {
    setExtracting(true);
    setError(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/alfresco/contracts/${contractId}/extract`,
        { use_openai: false },
        { headers: getAuthHeader() }
      );

      if (response.data.status === 'success') {
        setIntelligence(response.data.intelligence);
      } else {
        setError('Extraction failed');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to extract intelligence');
    } finally {
      setExtracting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <span className={`ml-3 ${theme.colors.textSecondary}`}>Loading intelligence...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-500/50">
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle className="h-5 w-5" />
            <p>{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!intelligence) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            AI Contract Intelligence
          </CardTitle>
          <CardDescription>
            Extract legal intelligence from this contract using AI
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className={`${theme.colors.textSecondary} mb-4`}>
            No intelligence has been extracted yet. Click below to analyze this contract.
          </p>
          <Button
            onClick={extractIntelligence}
            disabled={extracting}
            className="w-full sm:w-auto"
          >
            {extracting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Extracting Intelligence...
              </>
            ) : (
              <>
                <Brain className="mr-2 h-4 w-4" />
                Extract Intelligence
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    );
  }

  const confidenceColor = intelligence.extraction_confidence >= 0.8
    ? 'bg-green-600/20 text-green-300 border border-green-500/30'
    : intelligence.extraction_confidence >= 0.6
    ? 'bg-yellow-600/20 text-yellow-300 border border-yellow-500/30'
    : 'bg-red-600/20 text-red-300 border border-red-500/30';

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                AI Contract Intelligence
              </CardTitle>
              <CardDescription>
                Extracted on {new Date(intelligence.extracted_at).toLocaleDateString()}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge className={confidenceColor}>
                {(intelligence.extraction_confidence * 100).toFixed(0)}% Confidence
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={extractIntelligence}
                disabled={extracting}
              >
                {extracting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  'Re-extract'
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Intelligence Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <IntelligenceCard
          title="Contracting Parties"
          icon="👥"
          value={intelligence.parties}
          description="Entities entering the agreement"
        />

        <IntelligenceCard
          title="Governing Jurisdiction"
          icon="⚖️"
          value={intelligence.jurisdiction}
          description="Applicable laws and regulations"
        />

        <IntelligenceCard
          title="Termination Clause"
          icon="🚪"
          value={intelligence.termination_summary}
          subtitle={intelligence.termination_notice_period}
          description="How the contract can be ended"
        />

        <IntelligenceCard
          title="Liability Limitations"
          icon="🛡️"
          value={intelligence.liability_summary}
          description="Caps on damages and responsibility"
        />

        <IntelligenceCard
          title="Confidentiality"
          icon="🔒"
          value={intelligence.confidentiality_duration || 'Not specified'}
          description="Duration of confidentiality obligations"
        />

        <IntelligenceCard
          title="Extraction Metadata"
          icon="📊"
          value={`${intelligence.vector_db_chunks} chunks analyzed`}
          subtitle={`${intelligence.relevant_chunks_used} relevant sections used`}
          description="Vector database statistics"
        />
      </div>

      {/* Raw Data (Collapsible) */}
      {intelligence.raw_data && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Raw Extraction Data</CardTitle>
          </CardHeader>
          <CardContent>
            <details className="cursor-pointer">
              <summary className={`text-sm ${theme.colors.textSecondary} hover:${theme.colors.textPrimary} transition-colors`}>
                Click to view full JSON
              </summary>
              <pre className={`mt-2 p-4 ${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-md text-xs overflow-auto max-h-96 text-green-400`}>
                {JSON.stringify(intelligence.raw_data, null, 2)}
              </pre>
            </details>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

const IntelligenceCard = ({ title, icon, value, subtitle, description }) => {
  const { theme } = useThemeStore();
  return (
    <Card className={`hover:shadow-lg hover:shadow-blue-500/10 transition-all hover:border ${theme.colors.surfaceBorder}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{icon}</span>
          <CardTitle className={`text-sm font-medium ${theme.colors.textSecondary}`}>
            {title}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <p className={`text-base font-semibold ${theme.colors.textPrimary} mb-1`}>
          {value || 'Not specified'}
        </p>
        {subtitle && (
          <p className={`text-sm ${theme.colors.primaryText} mb-2`}>
            {subtitle}
          </p>
        )}
        <p className={`text-xs ${theme.colors.textSecondary}`}>
          {description}
        </p>
      </CardContent>
    </Card>
  );
};

export default ContractIntelligence;
