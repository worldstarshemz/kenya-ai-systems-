import React from 'react';

const TrendChart = ({ data, title }) => {
  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <h3 className="text-white font-bold mb-4">{title}</h3>
      <div className="h-32 bg-slate-700 rounded flex items-end justify-around p-4 gap-1">
        {data && data.map((value, idx) => (
          <div
            key={idx}
            className="flex-1 bg-blue-600 rounded-t opacity-70 hover:opacity-100 transition-opacity"
            style={{ height: `${(value / Math.max(...data)) * 100}%`, minHeight: '8px' }}
            title={value}
          />
        ))}
      </div>
    </div>
  );
};

export default TrendChart;
