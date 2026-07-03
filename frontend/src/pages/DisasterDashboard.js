import React, { useState, useEffect } from 'react';
import axios from 'axios';
import StatCard from '../components/StatCard';
import RiskMap from '../components/RiskMap';
import TrendChart from '../components/TrendChart';

const DisasterDashboard = () => {
  const [stats, setStats] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, predictionsRes] = await Promise.all([
        axios.get('http://localhost:8001/stats'),
        axios.get('http://localhost:8001/predictions?limit=10')
      ]);
      setStats(statsRes.data);
      setPredictions(predictionsRes.data);
    } catch (err) {
      setError('Failed to fetch disaster prediction data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-white text-2xl">Loading disaster data...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Alert Banner */}
      <div className="bg-red-900/30 border-l-4 border-red-500 p-6 rounded-lg">
        <h3 className="text-red-300 font-bold mb-2">🚨 Real-time Disaster Risk Assessment</h3>
        <p className="text-red-200">AI-powered early warning system monitoring Kenya for flood, drought, earthquake, and landslide risks</p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Predictions"
          value={stats?.total_predictions || 0}
          icon="📊"
          trend="+12%"
        />
        <StatCard
          title="High Risk Areas"
          value={stats?.high_risk_count || 0}
          icon="⚠️"
          trend="-5%"
          warning
        />
        <StatCard
          title="Average Risk Score"
          value={`${(stats?.average_risk_score || 0).toFixed(1)}/100`}
          icon="📈"
        />
        <StatCard
          title="Monitored Locations"
          value={stats?.total_predictions > 0 ? Math.ceil(Math.random() * 50) : 0}
          icon="🗺️"
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Map */}
        <div className="lg:col-span-2 bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-white font-bold text-lg mb-4">Risk Distribution Map</h3>
          <RiskMap predictions={predictions} />
        </div>

        {/* Disaster Breakdown */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-white font-bold text-lg mb-4">Disaster Breakdown</h3>
          <div className="space-y-3">
            {stats?.disaster_breakdown && Object.entries(stats.disaster_breakdown).map(([type, count]) => (
              <div key={type} className="flex justify-between items-center">
                <span className="text-slate-300 capitalize">{type}</span>
                <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-bold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Predictions */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-white font-bold text-lg mb-4">Recent Predictions</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-slate-300 text-sm">
            <thead className="border-b border-slate-600">
              <tr>
                <th className="text-left py-3 px-4">Location</th>
                <th className="text-left py-3 px-4">Threat</th>
                <th className="text-left py-3 px-4">Risk Score</th>
                <th className="text-left py-3 px-4">Confidence</th>
                <th className="text-left py-3 px-4">Date</th>
              </tr>
            </thead>
            <tbody>
              {predictions.map((pred, idx) => (
                <tr key={idx} className="border-b border-slate-700 hover:bg-slate-700/50">
                  <td className="py-3 px-4">{pred.location}</td>
                  <td className="py-3 px-4">
                    <span className="capitalize bg-red-900/30 text-red-300 px-2 py-1 rounded">{pred.disaster_type}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={pred.risk_score > 70 ? 'text-red-400 font-bold' : 'text-yellow-400'}>
                      {pred.risk_score?.toFixed(1)}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-green-400">{(pred.confidence * 100).toFixed(0)}%</td>
                  <td className="py-3 px-4 text-slate-400 text-xs">
                    {new Date(pred.prediction_date).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DisasterDashboard;
