import { useEffect, useState } from 'react';
import { fetchDatasetRecords, fetchDatasetSummary } from '../services/api';

export default function DatasetPage() {
  const [summary, setSummary] = useState({});
  const [records, setRecords] = useState([]);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  useEffect(() => {
    const load = async () => {
      try {
        const summaryData = await fetchDatasetSummary();
        const recordsData = await fetchDatasetRecords();
        setSummary(summaryData);
        setRecords(recordsData);
      } catch (error) {
        console.error(error);
      }
    };
    load();
  }, []);

  const filteredRecords = records.filter((row) =>
    JSON.stringify(row).toLowerCase().includes(search.toLowerCase())
  );
  const pageSize = 8;
  const totalPages = Math.max(1, Math.ceil(filteredRecords.length / pageSize));
  const visibleRecords = filteredRecords.slice((page - 1) * pageSize, page * pageSize);

  const columnNames = Object.keys(records[0] || {});

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Dataset Explorer</h2>
          <p>Traffic congestion dataset overview and sample records</p>
        </div>
      </div>

      <div className="stats-grid compact">
        <div className="stat-card">
          <span>Rows</span>
          <strong>{summary.rows || 0}</strong>
        </div>
        <div className="stat-card">
          <span>Columns</span>
          <strong>{summary.columns || 0}</strong>
        </div>
        <div className="stat-card">
          <span>Missing</span>
          <strong>{Object.values(summary.missing_values || {}).reduce((a, b) => a + Number(b), 0)}</strong>
        </div>
        <div className="stat-card">
          <span>Duplicates</span>
          <strong>{summary.duplicate_count || 0}</strong>
        </div>
      </div>

      <div className="panel">
        <h3>Class Distribution</h3>
        <div className="list-stack">
          {Object.entries(summary.class_distribution || {}).map(([key, value]) => (
            <div className="distribution-row" key={key}>
              <span>{key}</span>
              <div className="progress-bar"><i style={{ width: `${Math.min(100, (value / (summary.rows || 1)) * 100)}%` }} /></div>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <div className="table-actions">
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search rows..." />
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {columnNames.map((column) => (
                  <th key={column}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visibleRecords.map((row, index) => (
                <tr key={`${index}-${page}`}>
                  {columnNames.map((column) => (
                    <td key={`${column}-${index}`}>{String(row[column] ?? '')}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="pagination">
          <button disabled={page === 1} onClick={() => setPage((prev) => prev - 1)}>Previous</button>
          <span>Page {page} / {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage((prev) => prev + 1)}>Next</button>
        </div>
      </div>
    </div>
  );
}
