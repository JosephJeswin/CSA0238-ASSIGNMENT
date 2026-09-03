import { useState } from 'react';
import DashboardPage from './pages/DashboardPage';
import DatasetPage from './pages/DatasetPage';
import PredictionPage from './pages/PredictionPage';
import RoutePage from './pages/RoutePage';
import ComparisonPage from './pages/ComparisonPage';
import NetworkPage from './pages/NetworkPage';
import TracePage from './pages/TracePage';

const navigation = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'dataset', label: 'Dataset Explorer' },
  { key: 'prediction', label: 'Congestion Prediction' },
  { key: 'route', label: 'Route Finder' },
  { key: 'comparison', label: 'Route Comparison' },
  { key: 'network', label: 'Network Map' },
  { key: 'trace', label: 'ACO Trace' },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderPage = () => {
    switch (activeTab) {
      case 'dataset':
        return <DatasetPage />;
      case 'prediction':
        return <PredictionPage />;
      case 'route':
        return <RoutePage />;
      case 'comparison':
        return <ComparisonPage />;
      case 'network':
        return <NetworkPage />;
      case 'trace':
        return <TracePage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-badge">AI</div>
          <div>
            <h1>Traffic ACO</h1>
            <small>Congestion & Routing</small>
          </div>
        </div>

        <nav className="nav-menu">
          {navigation.map((item) => (
            <button
              key={item.key}
              className={activeTab === item.key ? 'nav-item active' : 'nav-item'}
              onClick={() => setActiveTab(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="content-area">{renderPage()}</main>
    </div>
  );
}
