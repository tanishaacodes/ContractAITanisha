import { Activity } from 'lucide-react';
import { useEffect, useRef } from 'react';

export default function DriftGauge({ value }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    drawGauge();
  }, [value]);

  const drawGauge = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2 + 20;
    const radius = 80;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw background arc (gray)
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI * 0.75, Math.PI * 2.25);
    ctx.lineWidth = 12;
    ctx.strokeStyle = '#374151'; // gray-700
    ctx.stroke();

    // Determine color based on value
    let color;
    if (value < 40) {
      color = '#4ADE80'; // green-400
    } else if (value < 70) {
      color = '#FACC15'; // yellow-400
    } else {
      color = '#EF4444'; // red-500
    }

    // Draw value arc (colored)
    const angle = (value / 100) * 1.5 * Math.PI; // 1.5 PI = 270 degrees
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI * 0.75, Math.PI * 0.75 + angle);
    ctx.lineWidth = 12;
    ctx.strokeStyle = color;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Draw center circle
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius - 20, 0, Math.PI * 2);
    ctx.fillStyle = '#1F2937'; // gray-800
    ctx.fill();

    // Draw value text
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 28px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${Math.round(value)}%`, centerX, centerY - 5);

    // Draw label
    ctx.fillStyle = '#9CA3AF'; // gray-400
    ctx.font = '12px Inter, sans-serif';
    ctx.fillText('DRIFT', centerX, centerY + 20);
  };

  // Get status based on value
  const getStatus = () => {
    if (value < 40) return { text: 'Low Drift', color: 'text-green-400', bg: 'bg-green-900/20' };
    if (value < 70) return { text: 'Moderate Drift', color: 'text-yellow-400', bg: 'bg-yellow-900/20' };
    return { text: 'High Drift', color: 'text-red-400', bg: 'bg-red-900/20' };
  };

  const status = getStatus();

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center text-gray-300 mb-4">
        <Activity className="w-5 h-5 mr-2" />
        <h3 className="font-semibold">Drift Probability</h3>
      </div>

      {/* Gauge Canvas */}
      <div className="flex justify-center">
        <canvas
          ref={canvasRef}
          width={220}
          height={160}
          className="max-w-full"
        />
      </div>

      {/* Status Badge */}
      <div className="mt-4 text-center">
        <div className={`inline-flex px-4 py-2 rounded-full ${status.bg}`}>
          <span className={`text-sm font-semibold ${status.color}`}>
            {status.text}
          </span>
        </div>
      </div>

      {/* Description */}
      <p className="text-xs text-gray-500 text-center mt-4">
        {value < 40 && 'Clause remains close to original version'}
        {value >= 40 && value < 70 && 'Clause has moderate changes from original'}
        {value >= 70 && 'Clause has significantly deviated from original'}
      </p>
    </div>
  );
}
