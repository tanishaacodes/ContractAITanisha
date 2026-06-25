import { useState, useEffect } from 'react';
import { Sparkles, Loader } from 'lucide-react';
import api from '../utils/api';
import useThemeStore from '../store/themeStore';

export default function SuggestedQuestions({ onSelectQuestion, contractType = 'General' }) {
  const { theme } = useThemeStore();
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSuggestedQuestions();
  }, [contractType]);

  const loadSuggestedQuestions = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/chat/suggested-questions?contractType=${contractType}`);
      setQuestions(response.data.questions || []);
    } catch (err) {
      console.error('Failed to load suggested questions:', err);
      setError('Failed to load suggestions');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="w-6 h-6 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error || questions.length === 0) {
    return null;
  }

  return (
    <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-lg p-6 mb-6`}>
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-5 h-5 text-purple-500" />
        <h3 className={`text-lg font-semibold ${theme.colors.textPrimary}`}>Suggested Questions</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {questions.map((q) => (
          <button
            key={q.id}
            onClick={() => onSelectQuestion(q.question)}
            className={`text-left p-3 rounded-lg border ${theme.colors.surfaceBorder} hover:border-blue-500 hover:bg-blue-50/10 transition-all duration-200 group`}
          >
            <span className={`text-sm ${theme.colors.textPrimary} group-hover:text-blue-400`}>
              {q.question}
            </span>
            {q.category && (
              <span className={`inline-block mt-1 px-2 py-1 text-xs ${theme.colors.surfaceHover} ${theme.colors.textSecondary} rounded`}>
                {q.category}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
