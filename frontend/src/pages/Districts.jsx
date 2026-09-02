import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import '../styles/main.css';
import { getRainfallDisplay } from '../utils/rainfallFormat';

const PAGE_SIZE = 24; // Results per page

const Districts = () => {
  const [districts, setDistricts] = useState([]);
  const [states, setStates] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const navigate = useNavigate();

  // Load full district list once just to populate the state dropdown
  useEffect(() => {
    const fetchStateList = async () => {
      try {
        const res = await api.get('/api/districts'); // lightweight full list
        const uniqueStates = [...new Set(res.data.map(d => d.state_name))].filter(Boolean).sort();
        setStates(uniqueStates);
      } catch (err) {
        console.error("Failed to load state list", err);
      }
    };
    fetchStateList();
  }, []);

  // Debounced search effect
  useEffect(() => {
    const handler = setTimeout(async () => {
      try {
        setLoading(true);
        const params = {};
        if (searchTerm.trim()) params.query = searchTerm.trim();
        if (selectedState) params.state = selectedState;

        const res = await api.get('/api/districts/search', { params });
        setDistricts(res.data);
        setError('');
        setLoading(false);
      } catch (err) {
        console.error("Search failed", err);
        setError("Unable to retrieve groundwater data. Please try again later.");
        setLoading(false);
      }
    }, 250);

    return () => clearTimeout(handler);
  }, [searchTerm, selectedState]);

  const handleSearch = (e) => {
    if (e) e.preventDefault();
    setCurrentPage(1);
  };

  const handleClearSearch = async () => {
    setSearchTerm('');
    setSelectedState('');
    setCurrentPage(1);
    try {
      setLoading(true);
      const res = await api.get('/api/districts/search');
      setDistricts(res.data);
      // Do NOT overwrite states — they are loaded from the full list separately
      setLoading(false);
    } catch (err) {
      setError("Failed to reload districts.");
      setLoading(false);
    }
  };

  const handleCardClick = (id) => {
    navigate(`/districts/${id}`);
  };

  const getBadgeClass = (category) => {
    if (!category) return '';
    const cat = category.toLowerCase();
    if (cat === 'safe') return 'badge-safe';
    if (cat === 'semi-critical') return 'badge-semi-critical';
    if (cat === 'critical') return 'badge-critical';
    if (cat === 'over-exploited') return 'badge-over-exploited';
    return '';
  };

  // Pagination calculations
  const totalPages = Math.ceil(districts.length / PAGE_SIZE);
  const paginatedDistricts = districts.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  return (
    <div className="container-inner">
      <header className="page-header">
        <div>
          <h1 className="page-title">District Search</h1>
          <p className="page-subtitle">Search groundwater levels and rainfall parameters across Indian districts.</p>
        </div>
        {districts.length > 0 && (
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {districts.length.toLocaleString()} districts found
          </span>
        )}
      </header>

      {/* Search Filters Card */}
      <section className="card" style={{ marginBottom: '30px' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '15px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ flex: 2, minWidth: '250px', margin: 0 }}>
            <label className="form-label" htmlFor="district-search-input">District Name</label>
            <input
              id="district-search-input"
              type="text"
              className="form-control"
              placeholder="Search e.g. Ananthapuramu"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div className="form-group" style={{ flex: 1, minWidth: '180px', margin: 0 }}>
            <label className="form-label" htmlFor="state-select">State / UT</label>
            <select
              id="state-select"
              className="form-select"
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
            >
              <option value="">All States</option>
              {states.map((s, idx) => (
                <option key={idx} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <button type="submit" className="btn btn-primary" style={{ padding: '12px 30px' }}>
            Filter Results
          </button>
          {(searchTerm || selectedState) && (
            <button
              type="button"
              className="btn btn-outline"
              onClick={handleClearSearch}
              style={{ padding: '12px 20px', color: 'var(--color-critical)', borderColor: 'var(--color-critical)' }}
            >
              Clear ✕
            </button>
          )}
        </form>
      </section>

      {error && <div className="alert-box alert-danger">{error}</div>}

      {/* Districts List Results */}
      {loading ? (
        <div className="stats-grid">
          <div className="skeleton skeleton-card"></div>
          <div className="skeleton skeleton-card"></div>
          <div className="skeleton skeleton-card"></div>
          <div className="skeleton skeleton-card"></div>
        </div>
      ) : districts.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-state-icon">🔍</div>
          <p>No groundwater data available for these search parameters.</p>
        </div>
      ) : (
        <>
          <section className="stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
            {paginatedDistricts.map((d) => (
              <div 
                key={d.id} 
                className="card" 
                onClick={() => handleCardClick(d.id)}
                style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '10px' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <h3 className="card-title" style={{ margin: 0, fontSize: '1.2rem' }}>{d.district_name}</h3>
                  <span className={`badge ${getBadgeClass(d.assessment_category)}`}>
                    {d.assessment_category || 'Unknown'}
                  </span>
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  State: {d.state_name} {getRainfallDisplay(d).value !== 'N/A' && `• Period: ${getRainfallDisplay(d).period}`}
                </p>
                
                <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '10px', marginTop: '5px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Depth to Water Level</span>
                    <span style={{ fontSize: '0.98rem', fontWeight: '700', color: 'var(--primary-color)' }}>
                      {d.depth_to_water_level_m_bgl !== null && d.depth_to_water_level_m_bgl !== undefined ? `${d.depth_to_water_level_m_bgl.toFixed(2)} m bgl` : 'N/A'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{getRainfallDisplay(d).label}</span>
                    <span style={{ fontSize: '0.98rem', fontWeight: '700', color: 'var(--secondary-color)' }}>
                      {getRainfallDisplay(d).value}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Stage of Groundwater Extraction</span>
                    <span style={{ fontSize: '0.98rem', fontWeight: '700', color: '#f57c00' }}>
                      {d.stage_of_groundwater_extraction_percent !== null && d.stage_of_groundwater_extraction_percent !== undefined ? `${d.stage_of_groundwater_extraction_percent.toFixed(2)}%` : 'N/A'}
                    </span>
                  </div>
                </div>

              </div>
            ))}
          </section>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '12px', marginTop: '10px', marginBottom: '30px', flexWrap: 'wrap' }}>
              <button
                className="btn btn-outline"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                style={{ padding: '8px 20px', fontSize: '0.88rem' }}
              >
                ← Previous
              </button>

              {/* Page number pills */}
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', justifyContent: 'center' }}>
                {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                  // Show pages around current
                  let page;
                  if (totalPages <= 7) {
                    page = i + 1;
                  } else if (currentPage <= 4) {
                    page = i + 1;
                  } else if (currentPage >= totalPages - 3) {
                    page = totalPages - 6 + i;
                  } else {
                    page = currentPage - 3 + i;
                  }

                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '50%',
                        border: page === currentPage ? 'none' : '1.5px solid var(--border-color)',
                        background: page === currentPage ? 'var(--primary-color)' : 'var(--surface-color)',
                        color: page === currentPage ? 'white' : 'var(--text-main)',
                        cursor: 'pointer',
                        fontWeight: page === currentPage ? 700 : 400,
                        fontSize: '0.88rem',
                        transition: 'all 0.15s',
                        fontFamily: 'inherit',
                      }}
                    >
                      {page}
                    </button>
                  );
                })}
              </div>

              <button
                className="btn btn-outline"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                style={{ padding: '8px 20px', fontSize: '0.88rem' }}
              >
                Next →
              </button>

              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                Page {currentPage} of {totalPages} ({districts.length.toLocaleString()} total)
              </span>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Districts;
