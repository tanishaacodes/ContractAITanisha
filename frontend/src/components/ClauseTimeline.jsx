import { FileText, ArrowRight, Sparkles } from 'lucide-react';

export default function ClauseTimeline({ data }) {
  // Determine heat color based on drift probability
  const getHeatColor = (drift) => {
    if (drift < 0.4) return {
      border: 'border-green-500',
      bg: 'bg-green-900/20',
      text: 'text-green-400',
      label: 'Low Risk'
    };
    if (drift < 0.7) return {
      border: 'border-yellow-500',
      bg: 'bg-yellow-900/20',
      text: 'text-yellow-400',
      label: 'Medium Risk'
    };
    return {
      border: 'border-red-500',
      bg: 'bg-red-900/20',
      text: 'text-red-400',
      label: 'High Risk'
    };
  };

  const heatColor = getHeatColor(data.drift_probability);

  return (
    <div className="space-y-4">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center">
          <FileText className="w-6 h-6 mr-2 text-cyan-400" />
          Clause Evolution Timeline
        </h2>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${heatColor.bg} ${heatColor.text}`}>
          {heatColor.label}
        </span>
      </div>

      {/* Timeline Container */}
      <div className="relative">
        {/* Timeline Line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-cyan-500 via-yellow-500 to-red-500 opacity-30" />

        {/* Original Clause */}
        <ClauseBlock
          title="Original Clause"
          subtitle="Baseline version"
          text={data.original_text}
          icon={FileText}
          iconColor="text-cyan-400"
          borderColor="border-cyan-500"
          bgColor="bg-cyan-900/10"
          isFirst={true}
        />

        {/* Arrow */}
        <div className="flex justify-center my-4">
          <ArrowRight className="w-6 h-6 text-gray-600" />
        </div>

        {/* Current Clause */}
        <ClauseBlock
          title="Current Clause"
          subtitle={`Modified ${data.version_count || 0} time(s)`}
          text={data.current_text}
          icon={FileText}
          iconColor={heatColor.text}
          borderColor={heatColor.border}
          bgColor={heatColor.bg}
        />

        {/* Arrow */}
        <div className="flex justify-center my-4">
          <ArrowRight className="w-6 h-6 text-gray-600" />
        </div>

        {/* Predicted Drift */}
        <ClauseBlock
          title="Predicted Future Clause"
          subtitle="AI-generated prediction"
          text={data.predicted_text}
          icon={Sparkles}
          iconColor="text-purple-400"
          borderColor="border-purple-500"
          bgColor="bg-purple-900/10"
          isPrediction={true}
        />
      </div>
    </div>
  );
}

function ClauseBlock({ title, subtitle, text, icon: Icon, iconColor, borderColor, bgColor, isFirst, isPrediction }) {
  return (
    <div className={`relative pl-16 pr-4 py-4`}>
      {/* Timeline Dot */}
      <div className={`absolute left-6 top-6 w-5 h-5 rounded-full border-2 ${borderColor} ${bgColor} z-10`}>
        <div className={`absolute inset-1 rounded-full ${bgColor.replace('/10', '/50')}`} />
      </div>

      {/* Card */}
      <div className={`bg-gray-800 border ${borderColor} rounded-lg p-4 transition-all hover:shadow-lg hover:shadow-${borderColor.split('-')[1]}-500/20`}>
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center">
            <Icon className={`w-5 h-5 mr-2 ${iconColor}`} />
            <div>
              <h3 className="font-semibold text-white">{title}</h3>
              <p className="text-xs text-gray-500">{subtitle}</p>
            </div>
          </div>

          {isPrediction && (
            <span className="px-2 py-1 bg-purple-900/50 text-purple-400 rounded text-xs font-semibold">
              AI Prediction
            </span>
          )}
        </div>

        {/* Clause Text */}
        <div className={`${bgColor} rounded p-3 border ${borderColor}`}>
          <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
            {text}
          </p>
        </div>

        {/* Character Count */}
        <p className="text-xs text-gray-600 mt-2">
          {text.length} characters
        </p>
      </div>
    </div>
  );
}
