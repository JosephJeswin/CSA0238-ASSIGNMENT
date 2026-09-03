import { useEffect, useState } from 'react';
import { healthCheck, fetchDatasetSummary, fetchModelMetrics, trainModel } from '../services/api';

export default function DashboardPage() {
  const [health, setHealth] = useState({});
  const [summary, setSummary] = useState({});
  const [metrics, setMetrics] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [healthData, summaryData] = await Promise.all([healthCheck(), fetchDatasetSummary()]);
        setHealth(healthData);
        setSummary(summaryData);

        if (healthData.model_available) {
          const metricData = await fetchModelMetrics();
          setMetrics(metricData);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const train = async () => {
    try {
      const result = await trainModel();
      setMetrics(result.metrics);
      const healthData = await healthCheck();
      setHealth(healthData);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Academic Project Dashboard</h2>
          <p>AI-based traffic congestion detection and intelligent route optimization</p>
        </div>
        <button className="primary-btn" onClick={train}>Train Model</button>
      </div>

      {loading ? <p>Loading project metrics...</p> : (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <span>Dataset Size</span>
              <strong>{summary.rows || 0}</strong>
              <small>rows</small>
            </div>
            <div className="stat-card">
              <span>Congestion Classes</span>
              <strong>{summary.target_classes ? summary.target_classes.length : 0}</strong>
              <small>levels</small>
            </div>
            <div className="stat-card">
              <span>Model Accuracy</span>
              <strong>{metrics.accuracy ? (metrics.accuracy * 100).toFixed(2) : '0.00'}%</strong>
              <small>random forest</small>
            </div>
            <div className="stat-card">
              <span>Current Scenario</span>
              <strong>Normal</strong>
              <small>default route</small>
            </div>
            <div className="stat-card">
              <span>Latest Prediction</span>
              <strong>--</strong>
              <small>pending</small>
            </div>
            <div className="stat-card">
              <span>Latest Route</span>
              <strong>A → I</strong>
              <small>traffic aware</small>
            </div>
          </div>

          <div className="panel-grid">
            <div className="panel">
              <h3>System Status</h3>
              <ul className="detail-list">
                <li><span>Backend</span><strong>{health.backend_status || 'unknown'}</strong></li>
                <li><span>Model</span><strong>{health.model_available ? 'ready' : 'not trained'}</strong></li>
                <li><span>Dataset</span><strong>{health.dataset_available ? 'loaded' : 'missing'}</strong></li>
              </ul>
            </div>

            <div className="panel">
              <h3>Class Distribution</h3>
              <ul className="detail-list">
                {Object.entries(summary.class_distribution || {}).map(([label, count]) => (
                  <li key={label}><span>{label}</span><strong>{count}</strong></li>
                ))}
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
