import { FileText, Hash, ExternalLink, CheckCircle, Sparkles } from 'lucide-react';
import useThemeStore from '../store/themeStore';

export default function EnhancedMessage({ message }) {
  const { theme } = useThemeStore();
  const isUser = message.type === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6 animate-fade-in`}>
      <div className={`max-w-3xl ${isUser ? 'ml-12' : 'mr-12'}`}>
        {/* Message Header */}
        <div className={`flex items-center gap-2 mb-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <span className={`text-xs font-medium ${theme.colors.textTertiary}`}>
            {isUser ? 'You' : 'AI Assistant'}
          </span>
          {!isUser && (
            <Sparkles className="w-3 h-3 text-purple-500" />
          )}
          {message.timestamp && (
            <span className={`text-xs ${theme.colors.textSecondary}`}>
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>

        {/* Message Content */}
        <div
          className={`p-4 rounded-lg ${
            isUser
              ? `${theme.colors.primarySolid} ${theme.colors.textPrimary}`
              : `${theme.colors.surface} border ${theme.colors.surfaceBorder} ${theme.colors.textPrimary}`
          }`}
        >
          <div className="whitespace-pre-wrap">{message.content}</div>

          {/* Typing Indicator for Loading State */}
          {message.isTyping && (
            <div className="flex items-center gap-2 mt-2">
              <div className="flex space-x-1">
                <div className={`w-2 h-2 ${theme.colors.textSecondary} rounded-full animate-bounce`}></div>
                <div className={`w-2 h-2 ${theme.colors.textSecondary} rounded-full animate-bounce`} style={{ animationDelay: '0.1s' }}></div>
                <div className={`w-2 h-2 ${theme.colors.textSecondary} rounded-full animate-bounce`} style={{ animationDelay: '0.2s' }}></div>
              </div>
              <span className={`text-xs ${theme.colors.textTertiary}`}>AI is thinking...</span>
            </div>
          )}

          {/* Sources with Page Numbers */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className={`mt-4 pt-4 border-t ${theme.colors.surfaceBorder}`}>
              <div className="flex items-center gap-2 mb-3">
                <FileText className={`w-4 h-4 ${theme.colors.textTertiary}`} />
                <span className={`text-sm font-medium ${theme.colors.textPrimary}`}>
                  Sources ({message.sources.length})
                </span>
              </div>

              <div className="space-y-2">
                {message.sources.map((source, idx) => (
                  <div
                    key={idx}
                    className={`flex items-start gap-2 p-2 ${theme.colors.surfaceHover} rounded-lg hover:${theme.colors.surface} transition-colors`}
                  >
                    <FileText className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-medium ${theme.colors.textPrimary} truncate`}>
                          {source.filename || source.original_filename || 'Unknown Document'}
                        </span>
                        {source.pageNumbers && source.pageNumbers.length > 0 && (
                          <div className="flex items-center gap-1 flex-shrink-0">
                            <Hash className={`w-3 h-3 ${theme.colors.textTertiary}`} />
                            <span className={`text-xs ${theme.colors.textSecondary}`}>
                              Page{source.pageNumbers.length > 1 ? 's' : ''}: {source.pageNumbers.join(', ')}
                            </span>
                          </div>
                        )}
                      </div>
                      {source.text && (
                        <p className={`text-xs ${theme.colors.textSecondary} mt-1 line-clamp-2`}>
                          {source.text}
                        </p>
                      )}
                      {source.score && (
                        <div className="flex items-center gap-1 mt-1">
                          <CheckCircle className="w-3 h-3 text-green-500" />
                          <span className="text-xs text-green-600">
                            {Math.round(source.score * 100)}% relevant
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          {!isUser && message.actions && message.actions.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {message.actions.map((action, idx) => (
                <button
                  key={idx}
                  onClick={action.onClick}
                  className={`flex items-center gap-2 px-3 py-1.5 ${theme.colors.primarySolid} hover:${theme.colors.primaryHover} ${theme.colors.textPrimary} text-sm rounded-lg transition-colors`}
                >
                  {action.icon}
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Cached Indicator */}
        {message.wasCached && (
          <div className="flex items-center gap-1 mt-1 text-xs text-green-600">
            <CheckCircle className="w-3 h-3" />
            <span>Instant response (cached)</span>
          </div>
        )}

        {/* Response Time */}
        {message.responseTime && (
          <div className={`flex items-center gap-1 mt-1 text-xs ${theme.colors.textTertiary}`}>
            <span>Response time: {message.responseTime}ms</span>
          </div>
        )}
      </div>
    </div>
  );
}
