import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Zap, Clock, Cpu, CheckCircle, Lightbulb } from 'lucide-react';

const FastProcessing = () => {
  const navigate = useNavigate();

  const processingSteps = [
    {
      number: '1',
      title: 'File Upload',
      description: 'Upload your contract in DOCX or image format',
      time: '< 1s',
      icon: '📤',
    },
    {
      number: '2',
      title: 'Text Extraction',
      description: 'Automatically extract text using OCR or document parsing',
      time: '< 2s',
      icon: '📄',
    },
    {
      number: '3',
      title: 'AI Classification',
      description: 'Classify contract type (NDA, MSA, SOW, PO, etc.)',
      time: '< 1s',
      icon: '🤖',
    },
    {
      number: '4',
      title: 'Results Display',
      description: 'Get instant results with extracted text and classification',
      time: '< 1s',
      icon: '✅',
    },
  ];

  const performanceMetrics = [
    {
      title: 'Document Size',
      value: 'Up to 25MB',
      icon: '📦',
    },
    {
      title: 'Average Processing',
      value: '< 5 seconds',
      icon: '⚡',
    },
    {
      title: 'Extraction Accuracy',
      value: '95%+',
      icon: '🎯',
    },
    {
      title: 'Concurrent Processing',
      value: 'Unlimited',
      icon: '♾️',
    },
  ];

  const supportedFormats = [
    {
      format: 'DOCX',
      description: 'Microsoft Word documents',
      icon: '📝',
    },
    {
      format: 'PNG',
      description: 'Scanned documents & images',
      icon: '🖼️',
    },
    {
      format: 'JPG / JPEG',
      description: 'Photograph-based documents',
      icon: '📸',
    },
  ];

  const advantages = [
    {
      title: 'Lightning Fast',
      description: 'Process multiple contracts in seconds, not hours',
      icon: '⚡',
    },
    {
      title: 'High Accuracy',
      description: 'Advanced OCR and text extraction technology',
      icon: '🎯',
    },
    {
      title: 'Scalable',
      description: 'Handle unlimited concurrent uploads',
      icon: '📈',
    },
    {
      title: 'Reliable',
      description: 'Enterprise-grade infrastructure with 99.9% uptime',
      icon: '🛡️',
    },
    {
      title: 'Intelligent',
      description: 'AI-powered classification and risk analysis',
      icon: '🧠',
    },
    {
      title: 'Secure',
      description: 'End-to-end encryption and data protection',
      icon: '🔐',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header with Back Button */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/dashboard')}
          className="p-2 hover:bg-slate-800 rounded-lg transition"
        >
          <ArrowLeft className="w-6 h-6 text-blue-400" />
        </button>
        <div>
          <h1 className="text-4xl font-bold text-white flex items-center gap-2">
            <Zap className="h-8 w-8 text-blue-400" />
            Fast Processing
          </h1>
            <p className="text-slate-400">Process contracts in seconds with advanced AI technology</p>
          </div>
        </div>

        {/* Processing Pipeline */}
        <div>
          <h3 className="text-2xl font-bold text-white mb-8">How It Works</h3>
          <div className="space-y-4">
            {processingSteps.map((step) => (
              <div key={step.number} className="flex gap-6 items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-blue-900/30 border-2 border-blue-600">
                    <span className="text-2xl">{step.icon}</span>
                  </div>
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-white text-lg">{step.title}</h4>
                    <span className="bg-blue-900/30 text-blue-300 text-xs font-semibold px-3 py-1 rounded-full">
                      {step.time}
                    </span>
                  </div>
                  <p className="text-slate-300">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-8 text-center">
            <p className="text-2xl font-bold text-blue-400">Total Processing Time: ~5 seconds</p>
          </div>
        </div>

        {/* Performance Metrics */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <Cpu className="w-6 h-6 text-blue-400" />
            <h3 className="text-2xl font-bold text-white">Performance Metrics</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {performanceMetrics.map((metric) => (
              <div key={metric.title} className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center hover:border-slate-700 transition">
                <div className="text-4xl mb-3">{metric.icon}</div>
                <p className="text-slate-400 text-sm mb-2">{metric.title}</p>
                <p className="text-2xl font-bold text-blue-400">{metric.value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Supported Formats */}
        <div>
          <h3 className="text-2xl font-bold text-white mb-6">Supported File Formats</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {supportedFormats.map((fmt) => (
              <div key={fmt.format} className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition">
                <p className="text-4xl mb-3">{fmt.icon}</p>
                <p className="font-semibold text-white mb-2">{fmt.format}</p>
                <p className="text-slate-300 text-sm">{fmt.description}</p>
              </div>
            ))}
          </div>
          <div className="mt-6 bg-blue-900/30 border border-blue-800 rounded-xl p-4 flex gap-3">
            <Lightbulb className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <p className="text-blue-300 text-sm">
              <strong>Tip:</strong> For PDF documents, export as images (PNG/JPG) to use OCR processing for fastest results.
            </p>
          </div>
        </div>

        {/* Advantages */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <CheckCircle className="w-6 h-6 text-blue-400" />
            <h3 className="text-2xl font-bold text-white">Why Our Processing is the Fastest</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {advantages.map((advantage) => (
              <div key={advantage.title} className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition">
                <div className="flex items-start gap-4">
                  <span className="text-3xl">{advantage.icon}</span>
                  <div>
                    <h4 className="font-semibold text-white mb-2">{advantage.title}</h4>
                    <p className="text-slate-300 text-sm">{advantage.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Comparison */}
        <div>
          <h3 className="text-2xl font-bold text-white mb-6">ContractAI vs Manual Processing</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900">
                  <th className="px-6 py-4 text-left text-sm font-semibold text-white">Metric</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-white">ContractAI</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-white">Manual Review</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-slate-800 hover:bg-slate-900/50">
                  <td className="px-6 py-4 text-slate-300">Time per Contract</td>
                  <td className="px-6 py-4 text-blue-400 font-semibold">~5 seconds</td>
                  <td className="px-6 py-4 text-slate-400">2-8 hours</td>
                </tr>
                <tr className="border-b border-slate-800 hover:bg-slate-900/50">
                  <td className="px-6 py-4 text-slate-300">Cost per Contract</td>
                  <td className="px-6 py-4 text-blue-400 font-semibold">Minimal</td>
                  <td className="px-6 py-4 text-slate-400">$200-$500</td>
                </tr>
                <tr className="border-b border-slate-800 hover:bg-slate-900/50">
                  <td className="px-6 py-4 text-slate-300">Accuracy</td>
                  <td className="px-6 py-4 text-blue-400 font-semibold">95%+</td>
                  <td className="px-6 py-4 text-slate-400">95-98%</td>
                </tr>
                <tr className="border-b border-slate-800 hover:bg-slate-900/50">
                  <td className="px-6 py-4 text-slate-300">Consistency</td>
                  <td className="px-6 py-4 text-blue-400 font-semibold">100%</td>
                  <td className="px-6 py-4 text-slate-400">Variable</td>
                </tr>
                <tr className="hover:bg-slate-900/50">
                  <td className="px-6 py-4 text-slate-300">Risk Detection</td>
                  <td className="px-6 py-4 text-blue-400 font-semibold">Automated</td>
                  <td className="px-6 py-4 text-slate-400">Manual</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      {/* Action Button */}
      <div className="flex gap-4 justify-end">
        <button
          onClick={() => navigate('/upload')}
          className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition shadow-lg"
        >
          Experience Fast Processing
        </button>
      </div>
    </div>
  );
};

export default FastProcessing;
