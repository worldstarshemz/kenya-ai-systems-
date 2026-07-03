import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import DisasterDashboard from './pages/DisasterDashboard';
import SmartCityDashboard from './pages/SmartCityDashboard';
import RoadDamageDashboard from './pages/RoadDamageDashboard';
import CropDiseaseDashboard from './pages/CropDiseaseDashboard';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('disaster');

  const menuItems = [
    { id: 'disaster', label: '⚠️ Disaster Prediction', icon: '🚨' },
    { id: 'smart-city', label: '🏙️ Smart City Twin', icon: '🌆' },
    { id: 'road-damage', label: '🛣️ Road Damage', icon: '🚗' },
    { id: 'crop-disease', label: '🌾 Crop Disease', icon: '🌱' }
  ];

  return (
    <Router>
      <div className="App min-h-screen bg-gradient-to-br from-blue-900 via-slate-800 to-slate-900">
        {/* Header */}
        <header className="bg-gradient-to-r from-blue-900 to-blue-800 text-white shadow-2xl">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-4xl font-bold">🇰🇪 Kenya AI Systems</h1>
                <p className="text-blue-200 mt-2">Integrated Intelligence for National Infrastructure</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-blue-300">Last Updated: {new Date().toLocaleTimeString()}</p>
              </div>
            </div>

            {/* Navigation Tabs */}
            <nav className="flex gap-2 overflow-x-auto pb-2">
              {menuItems.map(item => (
                <Link
                  key={item.id}
                  to={`/${item.id}`}
                  onClick={() => setActiveTab(item.id)}
                  className={`px-4 py-2 rounded-lg font-semibold transition-all whitespace-nowrap ${
                    activeTab === item.id
                      ? 'bg-white text-blue-900 shadow-lg'
                      : 'bg-blue-700 text-white hover:bg-blue-600'
                  }`}
                >
                  {item.icon} {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/disaster" element={<DisasterDashboard />} />
            <Route path="/smart-city" element={<SmartCityDashboard />} />
            <Route path="/road-damage" element={<RoadDamageDashboard />} />
            <Route path="/crop-disease" element={<CropDiseaseDashboard />} />
            <Route path="/" element={<DisasterDashboard />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-slate-900 text-slate-400 py-8 mt-16 border-t border-slate-700">
          <div className="max-w-7xl mx-auto px-4 text-center">
            <p>© 2026 Kenya AI Systems. Powering Smart Infrastructure with Artificial Intelligence.</p>
            <p className="text-xs mt-2">Built with ❤️ for Kenya's Digital Future</p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
