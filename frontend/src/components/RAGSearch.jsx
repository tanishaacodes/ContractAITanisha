import { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Search, Loader2, FileText, AlertCircle } from 'lucide-react';
import useThemeStore from '../store/themeStore';
import { config } from '../config/api.config';

const API_BASE_URL = config.API_BASE_URL;

const RAGSearch = () => {
  const { theme } = useThemeStore();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  const handleSearch = async (e) => {
    e?.preventDefault();

    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await axios.get(
        `${API_BASE_URL}/alfresco/query`,
        {
          params: { q: query, k: 5 },
          headers: getAuthHeader()
        }
      );

      if (response.data.status === 'success') {
        setResults(response.data);
      } else {
        setError('Search failed');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch(e);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            RAG-Powered Contract Search
          </CardTitle>
          <CardDescription>
            Ask questions about your contracts in natural language
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="flex-1">
              <Input
                placeholder="e.g., What are the termination clauses in my contracts?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-full"
                disabled={loading}
              />
            </div>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search
                </>
              )}
            </Button>
          </form>

          {/* Example Queries */}
          <div className="mt-4">
            <p className="text-sm text-muted-foreground mb-2">Try asking:</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_QUERIES.map((example, idx) => (
                <Badge
                  key={idx}
                  variant="outline"
                  className="cursor-pointer hover:bg-primary hover:text-primary-foreground"
                  onClick={() => setQuery(example)}
                >
                  {example}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <Card className="border-red-500/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-400">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {results && (
        <div className="space-y-4">
          {/* Answer */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Answer</CardTitle>
              <CardDescription>
                Based on {results.total_results} relevant section(s) from your contracts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className={`${theme.colors.textPrimary} leading-relaxed`}>
                {results.answer}
              </p>
            </CardContent>
          </Card>

          {/* Relevant Chunks */}
          {results.relevant_chunks && results.relevant_chunks.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Relevant Contract Sections
                </CardTitle>
                <CardDescription>
                  Source passages used to generate the answer
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {results.relevant_chunks.map((chunk, idx) => (
                  <ChunkCard key={idx} chunk={chunk} index={idx} />
                ))}
              </CardContent>
            </Card>
          )}

          {/* No Results */}
          {results.total_results === 0 && (
            <Card>
              <CardContent className="p-6 text-center">
                <p className={theme.colors.textSecondary}>
                  No relevant sections found. Try rephrasing your query or upload more contracts.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

const ChunkCard = ({ chunk, index }) => {
  const { theme } = useThemeStore();
  const relevancePercentage = (chunk.relevance_score * 100).toFixed(0);
  const relevanceColor = chunk.relevance_score >= 0.8
    ? 'bg-green-600/20 text-green-300 border border-green-500/30'
    : chunk.relevance_score >= 0.6
    ? 'bg-yellow-600/20 text-yellow-300 border border-yellow-500/30'
    : `${theme.colors.surfaceHover} ${theme.colors.textPrimary} border ${theme.colors.surfaceBorder}`;

  return (
    <div className={`p-4 border ${theme.colors.surfaceBorder} rounded-lg ${theme.colors.surfaceHover} hover:${theme.colors.surface} transition-colors`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <Badge variant="outline">Source {index + 1}</Badge>
          {chunk.contract_name && (
            <span className={`text-xs ${theme.colors.textSecondary}`}>
              Contract: {chunk.contract_name}
            </span>
          )}
        </div>
        <Badge className={relevanceColor}>
          {relevancePercentage}% relevant
        </Badge>
      </div>
      <p className={`text-sm ${theme.colors.textPrimary} leading-relaxed`}>
        {chunk.text}
      </p>
      {chunk.chunk_index !== undefined && (
        <p className={`text-xs ${theme.colors.textSecondary} mt-2`}>
          Chunk #{chunk.chunk_index}
        </p>
      )}
    </div>
  );
};

const EXAMPLE_QUERIES = [
  'What are the termination clauses?',
  'Which contracts have arbitration?',
  'What are the payment terms?',
  'Show me liability limitations',
  'What jurisdictions govern these contracts?'
];

export default RAGSearch;
