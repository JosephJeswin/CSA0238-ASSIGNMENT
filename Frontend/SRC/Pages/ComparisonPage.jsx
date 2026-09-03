import { useState } from 'react';
import { compareRoutes } from '../services/api';

export default function ComparisonPage() {
  const [request, setRequest] = useState({ source: 'A', destination: 'I', scenario: 'Accident Incident', aco_parameters: { number_of_ants: 20, number_of_iterations: 50, alpha: 1.0, beta: 2.0, evaporation_rate: 0.5, pheromone_constant: 100 } });
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      const response = await compareRoutes(request);
      setResult(response);
      setError('');
    } catch (submitError) {
      setError(submitError.message);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Route Comparison</h2>
          <p>Distance-only route compared with traffic-aware ACO path</p>
        </div>
      </div>

      <div className="two-column-layout">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label>
              <span>Source</span>
              <input value={request.source} onChange={(e) => setRequest({ ...request, source: e.target.value.toUpperCase() })} />
            </label>
            <label>
              <span>Destination</span>
              <input value={request.destination} onChange={(e) => setRequest({ ...request, destination: e.target.value.toUpperCase() })} />
            </label>
            <label>
              <span>Scenario</span>
              <select value={request.scenario} onChange={(e) => setRequest({ ...request, scenario: e.target.value })}>
                <option>Normal</option>
                <option>Morning Rush Hour</option>
                <option>Accident Incident</option>
                <option>Bad Weather Storm</option>
              </select>
            </label>
          </div>
          <button className="primary-btn" type="submit">Compare Routes</button>
        </form>

        <div className="panel result-panel">
          {error ? <p className="error-text">{error}</p> : null}
          {result ? (
            <>
              <h3>Comparison Summary</h3>
              <ul className="detail-list">
                <li><span>Time saved</span><strong>{result.time_saving.toFixed(1)}</strong></li>
                <li><span>Extra distance</span><strong>{result.extra_distance.toFixed(1)} km</strong></li>
                <li><span>Avoided congested road</span><strong>{result.avoided_congested_road}</strong></li>
              </ul>

              <div className="comparison-box">
                <div>
                  <h4>Distance-only</h4>
                  <p>{result.distance_only.route.join(' → ')}</p>
                  <small>{result.distance_only.distance.toFixed(1)} km</small>
                </div>
                <div>
                  <h4>Traffic-aware</h4>
                  <p>{result.traffic_aware.route.join(' → ')}</p>
                  <small>{result.traffic_aware.distance.toFixed(1)} km</small>
                </div>
              </div>
            </>
          ) : (
            <p>Choose a scenario and compare route alternatives.</p>
          )}
        </div>
      </div>
    </div>
  );
}
