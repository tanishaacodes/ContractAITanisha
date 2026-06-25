import React from 'react';
import { Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

/**
 * Trust Radar Chart Component
 * Visualizes trust dimensions: enforceability, negotiability, clarity, litigation survival
 */
const TrustRadarChart = ({ trustData }) => {
  const data = {
    labels: [
      'Enforceability',
      'Negotiability',
      'Clarity',
      'Litigation Survival'
    ],
    datasets: [
      {
        label: 'Trust Scores',
        data: [
          trustData.enforceability || 0,
          trustData.negotiability || 0,
          1 - (trustData.ambiguity || 0.5),  // Invert ambiguity for readability
          trustData.litigation_survival || 0
        ],
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 2,
        pointBackgroundColor: 'rgb(59, 130, 246)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgb(59, 130, 246)'
      }
    ]
  };

  const options = {
    scales: {
      r: {
        angleLines: {
          color: 'rgba(255, 255, 255, 0.1)'
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        },
        pointLabels: {
          color: '#e5e7eb',
          font: {
            size: 12
          }
        },
        ticks: {
          color: '#9ca3af',
          backdropColor: 'transparent',
          min: 0,
          max: 1,
          stepSize: 0.2
        }
      }
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.9)',
        titleColor: '#fff',
        bodyColor: '#e5e7eb',
        borderColor: 'rgba(59, 130, 246, 0.5)',
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            return `${context.label}: ${(context.parsed.r * 100).toFixed(0)}%`;
          }
        }
      }
    },
    maintainAspectRatio: true
  };

  return (
    <div className="w-full h-64 flex items-center justify-center">
      <Radar data={data} options={options} />
    </div>
  );
};

export default TrustRadarChart;
