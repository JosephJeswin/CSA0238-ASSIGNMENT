import { useState } from 'react';
import { predictCongestion } from '../services/api';

const defaultPayload = {
  speed_kph: 58,
  vehicle_count: 220,
  traffic_density: 0.41,
  road_occupancy: 0.28,
  average_delay_sec: 18,
  traffic_flow: 980,
  queue_length: 12,
  acceleration: 0.8,
  weather_condition: 'Clear',
  time_period: 'Morning',
  road_type: 'Highway',
  incident_status: 'None',
  signal_timing: 'Adaptive',
  environment_type: 'Urban',
};

export default function PredictionPage() {
  const [payload, setPayload] = useState(defaultPayload);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleChange = (event) => {
    const { name, value } = event.target;
    setPayload((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    try {
      const response = await predictCongestion({
        ...payload,
        speed_kph: Number(payload.speed_kph),
        vehicle_count: Number(payload.vehicle_count),
        traffic_density: Number(payload.traffic_density),
        road_occupancy: Number(payload.road_occupancy),
        average_delay_sec: Number(payload.average_delay_sec),
        traffic_flow: Number(payload.traffic_flow),
        queue_length: Number(payload.queue_length),
        acceleration: Number(payload.acceleration),
      });
      setResult(response);
    } catch (submitError) {
      setError(submitError.message);
      setResult(null);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Congestion Prediction</h2>
          <p>Traffic conditions input and congestion class estimation</p>
        </div>
      </div>

      <div className="two-column-layout">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <div className="form-grid">
            {Object.entries(payload).map(([key, value]) => (
              <label key={key}>
                <span>{key.replace(/_/g, ' ')}</span>
                <input name={key} value={value} onChange={handleChange} />
              </label>
            ))}
          </div>
          <button className="primary-btn" type="submit">Predict Congestion</button>
        </form>

        <div className="panel result-panel">
          {error ? <p className="error-text">{error}</p> : null}
          {result ? (
            <>
              <h3>Prediction Result</h3>
              <div className="result-card">
                <span>Class</span>
                <strong>{result.predicted_class}</strong>
                <small>confidence {result.confidence.toFixed(2)}</small>
              </div>

              <h4>Probability Breakdown</h4>
              <div className="list-stack">
                {Object.entries(result.probabilities).map(([key, value]) => (
                  <div className="distribution-row" key={key}>
                    <span>{key}</span>
                    <div className="progress-bar"><i style={{ width: `${(value * 100).toFixed(2)}%` }} /></div>
                    <strong>{(value * 100).toFixed(2)}%</strong>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p>Submit a traffic scenario to generate congestion predictions.</p>
          )}
        </div>
      </div>
    </div>
  );
}
