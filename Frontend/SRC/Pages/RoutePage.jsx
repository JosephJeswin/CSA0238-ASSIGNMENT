import { useState } from 'react';
import { findBestRoute } from '../services/api';

const defaultRoute = {
  source: 'A',
  destination: 'I',
  scenario: 'Normal',
  aco_parameters: {
    number_of_ants: 20,
    number_of_iterations: 50,
    alpha: 1.0,
    beta: 2.0,
    evaporation_rate: 0.5,
    pheromone_constant: 100,
  },
};

export default function RoutePage() {
  const [request, setRequest] = useState(defaultRoute);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    try {
      const response = await findBestRoute(request);
      setResult(response);
    } catch (submitError) {
      setError(submitError.message);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Route Finder</h2>
          <p>ACO-based traffic-aware route search across the 9-node network</p>
        </div>
      </div>

      <div className="two-column-layout">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label>
              <span>Source</span>
              <input value={request.source} onChange={(e) => setRequest((current) => ({ ...current, source: e.target.value.toUpperCase() }))} />
            </label>
            <label>
              <span>Destination</span>
              <input value={request.destination} onChange={(e) => setRequest((current) => ({ ...current, destination: e.target.value.toUpperCase() }))} />
            </label>
            <label>
              <span>Scenario</span>
              <select value={request.scenario} onChange={(e) => setRequest((current) => ({ ...current, scenario: e.target.value }))}>
                <option>Normal</option>
                <option>Morning Rush Hour</option>
                <option>Accident Incident</option>
                <option>Bad Weather Storm</option>
              </select>
            </label>
            <label>
              <span>Ants</span>
              <input type="number" value={request.aco_parameters.number_of_ants} onChange={(e) => setRequest((current) => ({ ...current, aco_parameters: { ...current.aco_parameters, number_of_ants: Number(e.target.value) } }))} />
            </label>
            <label>
              <span>Iterations</span>
              <input type="number" value={request.aco_parameters.number_of_iterations} onChange={(e) => setRequest((current) => ({ ...current, aco_parameters: { ...current.aco_parameters, number_of_iterations: Number(e.target.value) } }))} />
            </label>
            <label>
              <span>Alpha</span>
              <input type="number" step="0.1" value={request.aco_parameters.alpha} onChange={(e) => setRequest((current) => ({ ...current, aco_parameters: { ...current.aco_parameters, alpha: Number(e.target.value) } }))} />
            </label>
            <label>
              <span>Beta</span>
              <input type="number" step="0.1" value={request.aco_parameters.beta} onChange={(e) => setRequest((current) => ({ ...current, aco_parameters: { ...current.aco_parameters, beta: Number(e.target.value) } }))} />
            </label>
            <label>
              <span>Evaporation</span>
              <input type="number" step="0.1" value={request.aco_parameters.evaporation_rate} onChange={(e) => setRequest((current) => ({ ...current, aco_parameters: { ...current.aco_parameters, evaporation_rate: Number(e.target.value) } }))} />
            </label>
            <label>
              <span>Pheromone Constant</span>
              <input type="number" step="10" value={request.aco_parameters.pheromone_constant} onChange={(e) => setRequest((current) => ({ ...current, aco_parameters: { ...current.aco_parameters, pheromone_constant: Number(e.target.value) } }))} />
            </label>
          </div>
          <button className="primary-btn" type="submit">Find Best Route</button>
        </form>

        <div className="panel result-panel">
          {error ? <p className="error-text">{error}</p> : null}
          {result ? (
            <>
              <h3>Recommended Route</h3>
              <div className="route-card">
                <strong>{result.route.join(' → ')}</strong>
              </div>
              <ul className="detail-list">
                <li><span>Total distance</span><strong>{result.total_distance.toFixed(1)} km</strong></li>
                <li><span>Travel cost</span><strong>{result.total_cost.toFixed(1)}</strong></li>
                <li><span>Estimated time</span><strong>{result.estimated_time.toFixed(1)}</strong></li>
                <li><span>Iterations</span><strong>{result.iterations}</strong></li>
              </ul>
            </>
          ) : (
            <p>Set route parameters and optimize a traffic-aware path.</p>
          )}
        </div>
      </div>
    </div>
  );
}
