const API_BASE = 'http://localhost:5000';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
  }
  return data;
}

export const healthCheck = () => request('/api/health');
export const fetchDatasetSummary = () => request('/api/dataset/summary');
export const fetchDatasetRecords = () => request('/api/dataset/records');
export const trainModel = () => request('/api/model/train', { method: 'POST' });
export const fetchModelMetrics = () => request('/api/model/metrics');
export const predictCongestion = (payload) => request('/api/predict', { method: 'POST', body: JSON.stringify(payload) });
export const findBestRoute = (payload) => request('/api/route', { method: 'POST', body: JSON.stringify(payload) });
export const compareRoutes = (payload) => request('/api/route/compare', { method: 'POST', body: JSON.stringify(payload) });
export const fetchGraph = (scenario = 'Normal') => request(`/api/graph?scenario=${encodeURIComponent(scenario)}`);
export const fetchTrace = (scenario = 'Normal', source = 'A', destination = 'I', params = {}) =>
  request(`/api/aco/trace?scenario=${encodeURIComponent(scenario)}&source=${encodeURIComponent(source)}&destination=${encodeURIComponent(destination)}&number_of_ants=${params.number_of_ants || 20}&number_of_iterations=${params.number_of_iterations || 50}&alpha=${params.alpha || 1.0}&beta=${params.beta || 2.0}&evaporation_rate=${params.evaporation_rate || 0.5}&pheromone_constant=${params.pheromone_constant || 100}`);
