import React, { useState, useEffect } from 'react';
import axios from 'axios';
import StatCard from '../components/StatCard';

const SmartCityDashboard = () => {
  const [stats, setStats] = useState(null);
  const [assets, setAssets] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, assetsRes, eventsRes] = await Promise.all([
        axios.get('http://localhost:8002/stats'),
        axios.get('http://localhost:8002/assets?limit=5'),
        axios.get('http://localhost:8002/traffic/active')
      ]);
      setStats(statsRes.data);
      setAssets(assetsRes.data);
      setEvents(eventsRes.data);
    } catch (err) {
      console.error('Failed to fetch smart city data', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-white text-center py-12">Loading smart city data...</div>;

  return (
    <div className="space-y-8">
      <div className="bg-purple-900/30 border-l-4 border-purple-500 p-6 rounded-lg">
        <h3 className="text-purple-300 font-bold mb-2">🏙️ Kenya Smart City Digital Twin</h3>
        <p className="text-purple-200">Real-time 3D city simulation with IoT sensor integration and live traffic monitoring</p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Districts" value={stats?.total_districts || 0} icon="🗺️" />
        <StatCard title="City Assets" value={stats?.total_assets || 0} icon="🏗️" />
        <StatCard title="Active Sensors" value={stats?.sensor_readings_today || 0} icon="📡" />
        <StatCard title="Traffic Events" value={stats?.active_traffic_events || 0} icon="🚦" warning />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Asset Status */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-white font-bold mb-4">Infrastructure Status</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-green-400">✓ Operational</span>
              <span className="font-bold text-white">{stats?.asset_status?.operational || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-yellow-400">⚙ Maintenance</span>
              <span className="font-bold text-white">{stats?.asset_status?.maintenance || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-red-400">✗ Damaged</span>
              <span className="font-bold text-white">{stats?.asset_status?.damaged || 0}</span>
            </div>
          </div>
        </div>

        {/* Active Traffic Events */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-white font-bold mb-4">Active Traffic Events</h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {events.length > 0 ? (
              events.map((event, idx) => (
                <div key={idx} className="bg-slate-700/50 p-3 rounded border border-slate-600">
                  <div className="flex justify-between items-start">
                    <span className="font-semibold text-slate-200">{event.location}</span>
                    <span className={`text-xs font-bold px-2 py-1 rounded ${
                      event.severity >= 4 ? 'bg-red-900 text-red-300' : 'bg-yellow-900 text-yellow-300'
                    }`}>
                      Severity: {event.severity}/5
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm mt-1">{event.description}</p>
                </div>
              ))
            ) : (
              <p className="text-slate-400 text-center py-8">No active events</p>
            )}
          </div>
        </div>
      </div>

      {/* City Assets */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-white font-bold mb-4">Recent City Assets</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {assets.map((asset, idx) => (
            <div key={idx} className="bg-slate-700 p-4 rounded-lg border border-slate-600">
              <div className="text-2xl mb-2">🏢</div>
              <p className="text-white font-semibold text-sm">{asset.name}</p>
              <p className="text-slate-400 text-xs mt-1 capitalize">{asset.asset_type}</p>
              <p className={`text-xs mt-2 px-2 py-1 rounded w-fit ${
                asset.status === 'operational' ? 'bg-green-900 text-green-300' :
                asset.status === 'maintenance' ? 'bg-yellow-900 text-yellow-300' :
                'bg-red-900 text-red-300'
              }`}>
                {asset.status}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SmartCityDashboard;
