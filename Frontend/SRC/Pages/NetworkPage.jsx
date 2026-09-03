import { useEffect, useState } from 'react';
import { fetchGraph } from '../services/api';

export default function NetworkPage() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchGraph('Normal');
        setGraph(data);
      } catch (error) {
        console.error(error);
      }
    };
    load();
  }, []);

  const nodePositions = {
    A: { x: 130, y: 120 },
    B: { x: 250, y: 90 },
    C: { x: 390, y: 110 },
    D: { x: 170, y: 220 },
    E: { x: 310, y: 220 },
    F: { x: 430, y: 220 },
    G: { x: 210, y: 330 },
    H: { x: 340, y: 330 },
    I: { x: 500, y: 300 },
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Network Map</h2>
          <p>Urban road graph with congestion-aware edge conditions</p>
        </div>
      </div>

      <div className="panel">
        <div className="network-map">
          {graph.edges.map((edge, index) => {
            const start = nodePositions[edge.source];
            const end = nodePositions[edge.destination];
            return (
              <div
                key={`${edge.source}-${edge.destination}-${index}`}
                className={`road-link ${edge.congestion_level.toLowerCase().replace(/\s+/g, '-')}`}
                style={{
                  left: `${Math.min(start.x, end.x) + Math.abs(start.x - end.x) / 2}px`,
                  top: `${Math.min(start.y, end.y) + Math.abs(start.y - end.y) / 2}px`,
                  width: `${Math.max(40, Math.hypot(end.x - start.x, end.y - start.y))}px`,
                  transform: `rotate(${Math.atan2(end.y - start.y, end.x - start.x) * 180 / Math.PI}deg)`,
                }}
              >
                <span>{edge.congestion_level}</span>
              </div>
            );
          })}

          {graph.nodes.map((node) => (
            <div key={node} className="graph-node" style={{ left: `${nodePositions[node].x}px`, top: `${nodePositions[node].y}px` }}>
              {node}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
