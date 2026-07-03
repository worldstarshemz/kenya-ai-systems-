import React, { useState, useEffect } from 'react';
import axios from 'axios';
import StatCard from '../components/StatCard';

const CropDiseaseDashboard = () => {
  const [stats, setStats] = useState(null);
  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, detectionsRes] = await Promise.all([
        axios.get('http://localhost:8004/stats'),
        axios.get('http://localhost:8004/detections?limit=10')
      ]);
      setStats(statsRes.data);
      setDetections(detectionsRes.data);
    } catch (err) {
      console.error('Failed to fetch crop disease data', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-white text-center py-12">Loading crop disease data...</div>;

  const getDiseaseIcon = (disease) => {
    const icons = {
      'powdery_mildew': '🤍',
      'leaf_rust': '🟠',
      'blight': '🟤',
      'fusarium_wilt': '🟡',
      'septoria': '⚫',
      'healthy': '✅'
    };
    return icons[disease] || '🌾';
  };

  return (
    <div className="space-y-8">
      <div className="bg-green-900/30 border-l-4 border-green-500 p-6 rounded-lg">
        <h3 className="text-green-300 font-bold mb-2">🌾 Satellite-Based Crop Disease Detection</h3>
        <p className="text-green-200">AI-powered agricultural monitoring using satellite imagery and machine learning</p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Monitored Plots" value={stats?.total_plots || 0} icon="🚜" />
        <StatCard title="Detections" value={stats?.total_detections || 0} icon="🔍" />
        <StatCard title="Pending Alerts" value={stats?.pending_alerts || 0} icon="🚨" warning />
        <StatCard
          title="Avg NDVI Score"
          value={(stats?.avg_ndvi_score || 0).toFixed(2)}
          icon="📊"
        />
      </div>

      {/* Disease and Severity Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-white font-bold mb-4">Disease Detection Count</h3>
          <div className="space-y-3">
            {stats?.disease_breakdown && Object.entries(stats.disease_breakdown).map(([disease, count]) => (
              <div key={disease} className="flex justify-between items-center">
                <span className="text-slate-300">{getDiseaseIcon(disease)} {disease.replace('_', ' ')}</span>
                <span className="bg-green-600 text-white px-3 py-1 rounded-full text-sm font-bold">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-white font-bold mb-4">Severity Levels</h3>
          <div className="space-y-3">
            {stats?.severity_breakdown && Object.entries(stats.severity_breakdown).map(([severity, count]) => (
              <div key={severity} className="flex justify-between items-center">
                <span className="text-slate-300 capitalize">{severity}</span>
                <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                  severity === 'severe' ? 'bg-red-600' :
                  severity === 'high' ? 'bg-orange-600' :
                  severity === 'moderate' ? 'bg-yellow-600' :
                  'bg-blue-600'
                } text-white`}>{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Detections */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-white font-bold mb-4">Recent Disease Detections</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-slate-300 text-sm">
            <thead className="border-b border-slate-600">
              <tr>
                <th className="text-left py-3 px-4">Plot ID</th>
                <th className="text-left py-3 px-4">Disease</th>
                <th className="text-left py-3 px-4">Severity</th>
                <th className="text-left py-3 px-4">Confidence</th>
                <th className="text-left py-3 px-4">Infected Area %</th>
                <th className="text-left py-3 px-4">NDVI</th>
                <th className="text-left py-3 px-4">Date</th>
              </tr>
            </thead>
            <tbody>
              {detections.map((detection, idx) => (
                <tr key={idx} className="border-b border-slate-700 hover:bg-slate-700/50">
                  <td className="py-3 px-4 text-xs font-mono">{detection.plot_id?.substring(0, 8)}...</td>
                  <td className="py-3 px-4">
                    {getDiseaseIcon(detection.disease_name)} {detection.disease_name.replace('_', ' ')}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      detection.severity === 'severe' ? 'bg-red-900 text-red-300' :
                      detection.severity === 'high' ? 'bg-orange-900 text-orange-300' :
                      detection.severity === 'moderate' ? 'bg-yellow-900 text-yellow-300' :
                      'bg-blue-900 text-blue-300'
                    }`}>
                      {detection.severity}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-green-400">{(detection.confidence * 100).toFixed(0)}%</td>
                  <td className="py-3 px-4">{detection.infected_area_percentage?.toFixed(1) || 'N/A'}%</td>
                  <td className="py-3 px-4">{detection.ndvi_score?.toFixed(2) || 'N/A'}</td>
                  <td className="py-3 px-4 text-xs text-slate-400">
                    {new Date(detection.detected_at).toLocaleDateString()}
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

export default CropDiseaseDashboard;
