import { useEffect, useState } from 'react';
import { fetchTrace } from '../services/api';

export default function TracePage() {
  const [trace, setTrace] = useState([]);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await fetchTrace('Accident Incident', 'A', 'I', { number_of_ants: 20, number_of_iterations: 50 });
        setTrace(response.trace || []);
      } catch (error) {
        console.error(error);
      }
    };
    load();
  }, []);

  const maxCost = Math.max(...trace.map((row) => row.best_route_cost), 1);
  const points = trace.map((row, index) => {
    const x = (index / Math.max(1, trace.length - 1)) * 100;
    const y = 100 - (row.best_route_cost / maxCost) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>ACO Algorithm Trace</h2>
          <p>Iteration-by-iteration convergence and pheromone status</p>
        </div>
      </div>

      <div className="panel">
        <h3>Convergence Chart</h3>
        <svg viewBox="0 0 100 100" className="chart-svg" preserveAspectRatio="none">
          <polyline points={points} fill="none" stroke="#3867ff" strokeWidth="2" />
        </svg>
      </div>

      <div className="panel">
        <h3>Iteration Table</h3>
        <table>
          <thead>
            <tr>
              <th>Iteration</th>
              <th>Best Route</th>
              <th>Best Cost</th>
              <th>Average Cost</th>
              <th>Pheromone</th>
            </tr>
          </thead>
          <tbody>
            {trace.map((row) => (
              <tr key={row.iteration}>
                <td>{row.iteration}</td>
                <td>{row.best_route.join(' → ')}</td>
                <td>{row.best_route_cost.toFixed(2)}</td>
                <td>{row.average_route_cost.toFixed(2)}</td>
                <td>{row.pheromone.avg.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
