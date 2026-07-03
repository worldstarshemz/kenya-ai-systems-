import React, { useState, useEffect } from 'react';
import axios from 'axios';
import StatCard from '../components/StatCard';

const RoadDamageDashboard = () => {
  const [stats, setStats] = useState(null);
  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, detectionsRes] = await Promise.all([
        axios.get('http://localhost:8003/stats'),
        axios.get('http://localhost:8003/detections?limit=10')
      ]);
      setStats(statsRes.data);
      setDetections(detectionsRes.data);
    } catch (err) {
      console.error('Failed to fetch road damage data', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-white text-center py-12">Loading road damage data...</div>;

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-900 text-red-300';
      case 'high': return 'bg-orange-900 text-orange-300';
      case 'medium': return 'bg-yellow-900 text-yellow-300';
      case 'low': return 'bg-blue-900 text-blue-300';
      default: return 'bg-slate-600 text-slate-300';
    }
  };

  return (
    <div className="space-y-8">
      <div className="bg-orange-900/30 border-l-4 border-orange-500 p-6 rounded-lg">
        <h3 className="text-orange-300 font-bold mb-2">🛣️ AI Road Damage Detection</h3>
        <p className="text-orange-200">Automated road condition assessment using drone imagery and deep learning</p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Road Segments" value={stats?.total_segments || 0} icon="🛣️" />
        <StatCard title="Damage Detected" value={stats?.total_detections || 0} icon="🔍" />
        <StatCard title="Inspections" value={stats?.total_inspections || 0} icon="🚁" />
        <StatCard
          title="Avg Damage Area"
          value={`${(stats?.avg_damage_area_sqm || 0).toFixed(2)} m²`}
          icon="📏"
        />
      </div>

      {/* Damage Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-white font-bold mb-4">Damage Types</h3>
          <div className="space-y-3">
            {stats?.damage_breakdown && Object.entries(stats.damage_breakdown).map(([type, count]) => (
              <div key={type} className="flex justify-between items-center">
                <span className="text-slate-300 capitalize">{type}</span>
                <span className="bg-orange-600 text-white px-3 py-1 rounded-full text-sm font-bold">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-white font-bold mb-4">Severity Distribution</h3>
          <div className="space-y-3">
            {stats?.severity_breakdown && Object.entries(stats.severity_breakdown).map(([severity, count]) => (
              <div key={severity} className="flex justify-between items-center">
                <span className="text-slate-300 capitalize">{severity}</span>
                <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                  severity === 'critical' ? 'bg-red-600' :
                  severity === 'high' ? 'bg-orange-600' :
                  severity === 'medium' ? 'bg-yellow-600' :
                  'bg-blue-600'
                } text-white`}>{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Detections */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-white font-bold mb-4">Recent Damage Detections</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-slate-300 text-sm">
            <thead className="border-b border-slate-600">
              <tr>
                <th className="text-left py-3 px-4">Detection ID</th>
                <th className="text-left py-3 px-4">Damage Type</th>
                <th className="text-left py-3 px-4">Severity</th>
                <th className="text-left py-3 px-4">Confidence</th>
                <th className="text-left py-3 px-4">Area (m²)</th>
                <th className="text-left py-3 px-4">Date</th>
              </tr>
            </thead>
            <tbody>
              {detections.map((detection, idx) => (
                <tr key={idx} className="border-b border-slate-700 hover:bg-slate-700/50">
                  <td className="py-3 px-4 text-xs font-mono">{detection.detection_id?.substring(0, 8)}...</td>
                  <td className="py-3 px-4 capitalize">{detection.damage_type}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${getSeverityColor(detection.severity)}`}>
                      {detection.severity}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-green-400">{(detection.confidence * 100).toFixed(0)}%</td>
                  <td className="py-3 px-4">{detection.damage_area_sqm?.toFixed(2) || 'N/A'}</td>
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

export default RoadDamageDashboard;
