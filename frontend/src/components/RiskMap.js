import React from 'react';

const RiskMap = ({ predictions }) => {
  return (
    <div className="w-full h-96 bg-slate-700 rounded-lg border border-slate-600 flex items-center justify-center relative overflow-hidden">
      {/* Map Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 to-green-900/20 opacity-30"></div>
      
      {/* Kenya Outline */}
      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 500 600" style={{ opacity: 0.2 }}>
        <path d="M 250 100 L 300 150 L 320 200 L 280 280 L 250 300 L 200 280 L 180 200 L 200 150 Z" fill="none" stroke="white" strokeWidth="2" />
      </svg>

      {/* Risk Points */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative w-full h-full">
          {predictions.map((pred, idx) => {
            // Normalize lat/long to map coordinates
            const x = ((pred.longitude + 180) / 360) * 100;
            const y = ((90 - pred.latitude) / 180) * 100;
            const riskIntensity = Math.min(100, pred.risk_score || 50);
            
            return (
              <div
                key={idx}
                className="absolute w-4 h-4 rounded-full transition-all hover:w-6 hover:h-6"
                style={{
                  left: `${x}%`,
                  top: `${y}%`,
                  backgroundColor: riskIntensity > 70 ? '#ef4444' : riskIntensity > 40 ? '#f59e0b' : '#3b82f6',
                  opacity: 0.7 + (riskIntensity / 100) * 0.3,
                  boxShadow: `0 0 ${10 + riskIntensity / 10}px ${riskIntensity > 70 ? '#ef4444' : '#f59e0b'}`
                }}
                title={`${pred.location}: ${pred.risk_score?.toFixed(1) || 'N/A'}/100`}
              />
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-slate-800/80 rounded p-3 text-xs text-slate-300 border border-slate-600">
        <p className="font-semibold mb-2 text-white">Risk Level</p>
        <div className="flex gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span>Low</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span>Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span>High</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskMap;
