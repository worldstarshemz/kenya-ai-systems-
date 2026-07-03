import React from 'react';

const StatCard = ({ title, value, icon, trend, warning }) => {
  return (
    <div className={`rounded-lg p-6 border ${
      warning
        ? 'bg-red-900/20 border-red-600'
        : 'bg-slate-800 border-slate-700'
    }`}>
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-slate-300 font-semibold">{title}</h3>
        <span className="text-3xl">{icon}</span>
      </div>
      <div className="flex justify-between items-end">
        <p className={`text-3xl font-bold ${
          warning ? 'text-red-300' : 'text-white'
        }`}>
          {value}
        </p>
        {trend && (
          <span className="text-xs text-green-400 bg-green-900/30 px-2 py-1 rounded">
            {trend}
          </span>
        )}
      </div>
    </div>
  );
};

export default StatCard;
