import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  BarChart, Bar, LineChart, Line, ComposedChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import api from '../services/api';
import WeatherCard from '../components/WeatherCard';
import ErrorBoundary from '../components/ErrorBoundary';
import weatherIconMap from '../utils/weatherIconMap';
import '../styles/main.css';
import '../styles/forecast.css';
import '../assets/weather-icons.min.css';

const SCENARIOS = [
  { key: 'normal', name: 'Normal Monsoon (Baseline)', icon: '🌤️', desc: 'Standard historical average rainfall with trend continuation.' },
  { key: 'drought', name: 'Deficit Monsoon / Drought (-20%)', icon: '☀️', desc: 'Reduced monsoon precipitation causing +15% extra irrigation draft.' },
  { key: 'surplus', name: 'Surplus Monsoon (+20%)', icon: '🌧️', desc: 'Above-average rainfall enhancing natural aquifer recharge.' },
  { key: 'conservation', name: 'Recharge & Conservation Active', icon: '💧', desc: 'Check dams, percolation tanks, and 25% micro-irrigation adoption.' },
];

const HORIZONS = [
  { years: 1, label: '1 Year' },
  { years: 2, label: '2 Years' },
  { years: 3, label: '3 Years' },
  { years: 5, label: '5 Years' },
];

const Forecast = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') === 'prediction' ? 'prediction' : 'weather';
  const initialDistrict = searchParams.get('district') || '';

  const [activeTab, setActiveTab] = useState(initialTab);
  const [selectedState, setSelectedState] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState(initialDistrict);
  const [statesList, setStatesList] = useState([]);
  const [districtsList, setDistrictsList] = useState([]);
  
  // Weather state
  const [forecast, setForecast] = useState(null);
  const [loadingWeather, setLoadingWeather] = useState(false);
  const [weatherError, setWeatherError] = useState('');

  // Prediction state
  const [prediction, setPrediction] = useState(null);
  const [loadingPrediction, setLoadingPrediction] = useState(false);
  const [predictionError, setPredictionError] = useState('');
  const [selectedScenario, setSelectedScenario] = useState('normal');
  const [selectedHorizon, setSelectedHorizon] = useState(5);

  const [loadingStates, setLoadingStates] = useState(true);

  // Fetch states on mount
  useEffect(() => {
    const fetchStates = async () => {
      try {
        const res = await api.get('/api/dashboard/state-statistics');
        const uniqueStates = res.data
          .map(s => s.state_name)
          .filter(Boolean)
          .sort((a, b) => a.localeCompare(b));
        setStatesList(uniqueStates);
        setLoadingStates(false);

        // If district provided in URL, auto-load
        if (initialDistrict) {
          const matchedDistrictState = res.data.find(d => d.district_name?.toLowerCase() === initialDistrict.toLowerCase());
          if (matchedDistrictState?.state_name) {
            setSelectedState(matchedDistrictState.state_name);
            handleStateChange(matchedDistrictState.state_name, initialDistrict);
          } else {
            handleDistrictChange(initialDistrict);
          }
        }
      } catch (err) {
        console.error("Failed to load states", err);
        setLoadingStates(false);
      }
    };
    fetchStates();
  }, []);

  const handleTabSwitch = (tab) => {
    setActiveTab(tab);
    setSearchParams(prev => {
      prev.set('tab', tab);
      if (selectedDistrict) prev.set('district', selectedDistrict);
      return prev;
    });
  };

  // State change handler
  const handleStateChange = async (state, preselectDistrict = '') => {
    setSelectedState(state);
    if (!preselectDistrict) {
      setSelectedDistrict('');
      setForecast(null);
      setPrediction(null);
    }
    setDistrictsList([]);
    if (!state) return;

    try {
      const res = await api.get(`/api/dashboard/state-statistics?state_name=${encodeURIComponent(state)}`);
      const districts = res.data
        .map(d => d.district_name)
        .filter(Boolean)
        .sort((a, b) => a.localeCompare(b));
      setDistrictsList(districts);

      if (preselectDistrict && districts.includes(preselectDistrict)) {
        setSelectedDistrict(preselectDistrict);
        fetchWeatherData(preselectDistrict);
        fetchPredictionData(preselectDistrict, selectedHorizon, selectedScenario);
      }
    } catch (err) {
      console.error("Failed to load districts", err);
    }
  };

  // District change handler
  const handleDistrictChange = (district) => {
    setSelectedDistrict(district);
    setForecast(null);
    setPrediction(null);
    setWeatherError('');
    setPredictionError('');
    if (!district) return;

    setSearchParams(prev => {
      prev.set('district', district);
      prev.set('tab', activeTab);
      return prev;
    });

    fetchWeatherData(district);
    fetchPredictionData(district, selectedHorizon, selectedScenario);
  };

  const fetchWeatherData = async (district) => {
    if (!district) return;
    setLoadingWeather(true);
    setWeatherError('');
    try {
      const res = await api.get(`/api/weather/forecast/${encodeURIComponent(district)}`);
      setForecast(res.data);
    } catch (err) {
      console.error("Weather forecast fetch failed", err);
      setWeatherError(err.response?.data?.detail || 'Unable to load weather forecast.');
    } finally {
      setLoadingWeather(false);
    }
  };

  const fetchPredictionData = async (district, horizon, scenario) => {
    if (!district) return;
    setLoadingPrediction(true);
    setPredictionError('');
    try {
      const res = await api.get(
        `/api/prediction/district/${encodeURIComponent(district)}?years_ahead=${horizon}&scenario=${scenario}`
      );
      setPrediction(res.data);
    } catch (err) {
      console.error("Prediction fetch failed", err);
      setPredictionError(err.response?.data?.detail || 'Unable to load future water level predictions.');
    } finally {
      setLoadingPrediction(false);
    }
  };

  const handleScenarioChange = (scenarioKey) => {
    setSelectedScenario(scenarioKey);
    if (selectedDistrict) {
      fetchPredictionData(selectedDistrict, selectedHorizon, scenarioKey);
    }
  };

  const handleHorizonChange = (years) => {
    setSelectedHorizon(years);
    if (selectedDistrict) {
      fetchPredictionData(selectedDistrict, years, selectedScenario);
    }
  };

  // Prepare combined data for prediction chart
  const combinedPredictionChartData = useMemo(() => {
    if (!prediction) return [];
    const hist = prediction.historical_series || [];
    const proj = prediction.projected_series || [];

    const data = [];

    // Add historical observations
    hist.forEach((h, idx) => {
      const isLastHist = idx === hist.length - 1;
      data.push({
        year: h.year,
        historical_depth: h.depth_to_water_level_m_bgl,
        projected_depth: isLastHist ? h.depth_to_water_level_m_bgl : null,
        conf_lower: isLastHist ? h.depth_to_water_level_m_bgl : null,
        conf_upper: isLastHist ? h.depth_to_water_level_m_bgl : null,
        soe: h.stage_of_extraction_percent,
        is_projected: false
      });
    });

    // Add projected points
    proj.forEach(p => {
      data.push({
        year: p.year,
        historical_depth: null,
        projected_depth: p.depth_to_water_level_m_bgl,
        conf_lower: p.confidence_lower_m_bgl,
        conf_upper: p.confidence_upper_m_bgl,
        soe: p.stage_of_extraction_percent,
        category: p.category,
        risk_level: p.risk_level,
        is_projected: true
      });
    });

    return data;
  }, [prediction]);

  // Weather formatting helpers
  const getImpactClass = (riskLevel) => {
    if (!riskLevel) return 'impact-safe';
    const r = riskLevel.toLowerCase();
    if (r.includes('over')) return 'impact-over-exploited';
    if (r.includes('critical') && !r.includes('semi')) return 'impact-critical';
    if (r.includes('semi')) return 'impact-semi-critical';
    return 'impact-safe';
  };

  const getRechargeBadgeClass = (potential) => {
    if (!potential) return 'recharge-minimal';
    const p = potential.toLowerCase();
    if (p === 'high') return 'recharge-high';
    if (p === 'moderate') return 'recharge-moderate';
    if (p === 'low') return 'recharge-low';
    return 'recharge-minimal';
  };

  const formatHourlyData = () => {
    if (!forecast?.hourly_rainfall) return [];
    return forecast.hourly_rainfall.map(h => {
      const dt = new Date(h.time);
      const label = dt.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
      const shortLabel = dt.toLocaleString([], { hour: '2-digit', minute: '2-digit' });
      return {
        ...h,
        label,
        shortLabel,
        hour: dt.getHours(),
        date: dt.toLocaleDateString([], { month: 'short', day: 'numeric' }),
      };
    });
  };

  const formatSoilData = () => {
    if (!forecast?.daily_forecast) return [];
    return forecast.daily_forecast.map(d => ({
      date: new Date(d.date).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' }),
      soil_moisture: d.soil_moisture != null ? +(d.soil_moisture * 100).toFixed(1) : null,
      et0: d.et0,
      rain: d.precipitation_sum,
    }));
  };

  return (
    <div className="container-inner">
      <header className="page-header">
        <div>
          <h1 className="page-title">🔮 Forecast & Future Water Level Prediction</h1>
          <p className="page-subtitle">
            Live precipitation intelligence, 7-day weather impact, and hydro-statistical multi-year groundwater level predictions.
          </p>
        </div>
        {selectedDistrict && (
          <span className="live-indicator">LIVE PREDICTIVE ENGINE</span>
        )}
      </header>

      {/* Navigation Tabs */}
      <div className="forecast-tabs">
        <button
          className={`forecast-tab-btn ${activeTab === 'prediction' ? 'active' : ''}`}
          onClick={() => handleTabSwitch('prediction')}
        >
          <span>🔮</span> Future Water Level Prediction <span className="tab-badge">AI Model</span>
        </button>
        <button
          className={`forecast-tab-btn ${activeTab === 'weather' ? 'active' : ''}`}
          onClick={() => handleTabSwitch('weather')}
        >
          <span>🌧️</span> 7-Day Rainfall & Weather Forecast <span className="tab-badge">Open-Meteo</span>
        </button>
      </div>

      {/* District & State Selector Card */}
      <section className="card" style={{ marginBottom: '24px' }}>
        <div className="forecast-selector-row">
          <div className="form-group">
            <label className="form-label">Select State</label>
            <select
              value={selectedState}
              onChange={(e) => handleStateChange(e.target.value)}
              disabled={loadingStates}
            >
              <option value="">-- Choose a State --</option>
              {statesList.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {selectedState && (
            <div className="form-group">
              <label className="form-label">Select District</label>
              <select
                value={selectedDistrict}
                onChange={(e) => handleDistrictChange(e.target.value)}
              >
                <option value="">-- Choose a District --</option>
                {districtsList.map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Prediction Controls (Scenario + Horizon) - Visible in Prediction Tab */}
        {activeTab === 'prediction' && selectedDistrict && (
          <div className="prediction-controls-row">
            <div>
              <div className="control-group-title">🌱 Simulation Scenario</div>
              <div className="scenario-pills-container">
                {SCENARIOS.map(scen => (
                  <button
                    key={scen.key}
                    className={`scenario-pill ${selectedScenario === scen.key ? 'active' : ''}`}
                    onClick={() => handleScenarioChange(scen.key)}
                    title={scen.desc}
                  >
                    <span>{scen.icon}</span>
                    <span>{scen.name}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="control-group-title">⏱️ Forecast Horizon</div>
              <div className="horizon-pills-container">
                {HORIZONS.map(h => (
                  <button
                    key={h.years}
                    className={`horizon-pill ${selectedHorizon === h.years ? 'active' : ''}`}
                    onClick={() => handleHorizonChange(h.years)}
                  >
                    {h.label} ({2026 + h.years})
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Empty Selection State */}
      {!selectedDistrict && (
        <div className="card" style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '3.5rem', marginBottom: '16px' }}>🔮</div>
          <h3 style={{ color: 'var(--text-main)', marginBottom: '8px' }}>Select an Indian District</h3>
          <p>
            Choose a state and district to generate AI hydro-statistical future water level predictions, scenario modeling, and live rainfall forecasts.
          </p>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────── */}
      {/* TAB 1: PREDICTIVE WATER LEVEL FORECASTING                     */}
      {/* ───────────────────────────────────────────────────────────── */}
      {activeTab === 'prediction' && selectedDistrict && (
        <>
          {loadingPrediction && (
            <div>
              <div className="skeleton skeleton-title"></div>
              <div className="prediction-hero-grid">
                <div className="skeleton skeleton-card"></div>
                <div className="skeleton skeleton-card"></div>
                <div className="skeleton skeleton-card"></div>
                <div className="skeleton skeleton-card"></div>
              </div>
              <div className="skeleton" style={{ height: '340px', marginTop: '20px' }}></div>
            </div>
          )}

          {predictionError && <div className="alert-box alert-danger">{predictionError}</div>}

          {prediction && !loadingPrediction && (
            <>
              {/* Prediction Hero Metrics Cards */}
              <div className="prediction-hero-grid">
                <div className="prediction-metric-card">
                  <div className="metric-header">
                    <span>Baseline ({prediction.baseline?.year})</span>
                    <span className="badge badge-safe">{prediction.baseline?.category}</span>
                  </div>
                  <div className="metric-val-main" style={{ color: 'var(--primary-color)' }}>
                    {prediction.baseline?.depth_to_water_level_m_bgl?.toFixed(2)} <span style={{ fontSize: '1rem', fontWeight: 600 }}>m bgl</span>
                  </div>
                  <div className="metric-subtext">
                    Stage of Extraction: <strong>{prediction.baseline?.stage_of_extraction_percent?.toFixed(1)}%</strong>
                  </div>
                </div>

                <div className="prediction-metric-card">
                  <div className="metric-header">
                    <span>Projected ({prediction.projected_series?.slice(-1)[0]?.year})</span>
                    <span className={`badge badge-${prediction.projected_series?.slice(-1)[0]?.category?.toLowerCase() || 'safe'}`}>
                      {prediction.projected_series?.slice(-1)[0]?.category}
                    </span>
                  </div>
                  <div className="metric-val-main" style={{ color: '#8b5cf6' }}>
                    {prediction.projected_series?.slice(-1)[0]?.depth_to_water_level_m_bgl?.toFixed(2)} <span style={{ fontSize: '1rem', fontWeight: 600 }}>m bgl</span>
                  </div>
                  <div className="metric-subtext">
                    80% Range: <strong>{prediction.projected_series?.slice(-1)[0]?.confidence_lower_m_bgl?.toFixed(1)} – {prediction.projected_series?.slice(-1)[0]?.confidence_upper_m_bgl?.toFixed(1)} m</strong>
                  </div>
                </div>

                <div className="prediction-metric-card">
                  <div className="metric-header">
                    <span>Projected Water Shift</span>
                    <span className="badge badge-outline">Δh</span>
                  </div>
                  <div
                    className="metric-val-main"
                    style={{
                      color: (prediction.projected_series?.slice(-1)[0]?.depth_to_water_level_m_bgl - prediction.baseline?.depth_to_water_level_m_bgl) > 0
                        ? 'var(--color-critical)'
                        : 'var(--color-safe)'
                    }}
                  >
                    {(prediction.projected_series?.slice(-1)[0]?.depth_to_water_level_m_bgl - prediction.baseline?.depth_to_water_level_m_bgl) > 0 ? '+' : ''}
                    {(prediction.projected_series?.slice(-1)[0]?.depth_to_water_level_m_bgl - prediction.baseline?.depth_to_water_level_m_bgl)?.toFixed(2)} <span style={{ fontSize: '1rem', fontWeight: 600 }}>m</span>
                  </div>
                  <div className="metric-subtext">
                    Historical Trend Rate: <strong>{prediction.baseline?.annual_trend_rate_m_per_year > 0 ? '+' : ''}{prediction.baseline?.annual_trend_rate_m_per_year} m/yr</strong>
                  </div>
                </div>

                <div className="prediction-metric-card">
                  <div className="metric-header">
                    <span>Projected SOE %</span>
                    <span className={`badge badge-${prediction.projected_series?.slice(-1)[0]?.risk_level?.toLowerCase() || 'safe'}`}>
                      {prediction.projected_series?.slice(-1)[0]?.risk_level} Risk
                    </span>
                  </div>
                  <div className="metric-val-main" style={{ color: 'var(--secondary-color)' }}>
                    {prediction.projected_series?.slice(-1)[0]?.stage_of_extraction_percent?.toFixed(1)} <span style={{ fontSize: '1rem', fontWeight: 600 }}>%</span>
                  </div>
                  <div className="metric-subtext">
                    Scenario: <strong>{prediction.selected_scenario?.name?.split(' ')[0]}</strong>
                  </div>
                </div>
              </div>

              {/* Main Interactive Forecast Chart */}
              <section className="card" style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '14px' }}>
                  <div>
                    <h3 className="card-title" style={{ margin: 0 }}>
                      📈 Groundwater Level Historical Trend & Multi-Year Projection
                    </h3>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px', margin: 0 }}>
                      Solid blue line: CGWB historical observations (1994–2026). Dashed purple line: Model projections under <strong>{prediction.selected_scenario?.name}</strong> with 80% confidence interval band.
                    </p>
                  </div>
                  <span className="badge badge-outline">Depth to Water Level (m bgl)</span>
                </div>

                <div style={{ minHeight: '340px' }}>
                  <ErrorBoundary>
                    <ResponsiveContainer width="100%" height={340}>
                      <ComposedChart data={combinedPredictionChartData} margin={{ top: 20, right: 30, left: 10, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.4} />
                        <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                        <YAxis
                          label={{ value: 'Depth (m bgl) — Higher is deeper', angle: -90, position: 'insideLeft', fontSize: 11 }}
                          tick={{ fontSize: 11 }}
                          domain={['auto', 'auto']}
                        />
                        <Tooltip
                          formatter={(value, name) => {
                            if (name === 'Historical Depth (m bgl)') return [`${value} m bgl`, name];
                            if (name === 'Projected Depth (m bgl)') return [`${value} m bgl`, name];
                            if (name === 'Upper Confidence Band') return [`${value} m bgl`, name];
                            return [value, name];
                          }}
                          labelFormatter={(label) => `Year: ${label}`}
                        />
                        <Legend />
                        <ReferenceLine y={8.0} stroke="#2e7d32" strokeDasharray="4 4" label={{ value: 'Safe Threshold (8m)', fill: '#2e7d32', fontSize: 10 }} />
                        <ReferenceLine y={14.0} stroke="#f57c00" strokeDasharray="4 4" label={{ value: 'Semi-Critical (14m)', fill: '#f57c00', fontSize: 10 }} />
                        <ReferenceLine y={20.0} stroke="#d32f2f" strokeDasharray="4 4" label={{ value: 'Critical (20m)', fill: '#d32f2f', fontSize: 10 }} />
                        
                        <Area
                          type="monotone"
                          dataKey="conf_upper"
                          fill="rgba(139, 92, 246, 0.12)"
                          stroke="rgba(139, 92, 246, 0.3)"
                          name="Upper Confidence Band"
                        />
                        <Line
                          type="monotone"
                          dataKey="historical_depth"
                          stroke="#0ea5e9"
                          strokeWidth={2.5}
                          dot={{ r: 4, fill: '#0ea5e9' }}
                          activeDot={{ r: 6 }}
                          name="Historical Depth (m bgl)"
                          connectNulls={false}
                        />
                        <Line
                          type="monotone"
                          dataKey="projected_depth"
                          stroke="#8b5cf6"
                          strokeWidth={2.5}
                          strokeDasharray="6 6"
                          dot={{ r: 5, fill: '#8b5cf6' }}
                          activeDot={{ r: 7 }}
                          name="Projected Depth (m bgl)"
                          connectNulls={true}
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </ErrorBoundary>
                </div>
              </section>

              {/* Multi-Scenario Sensitivity Cards */}
              <section className="card" style={{ marginBottom: '24px' }}>
                <h3 className="card-title" style={{ marginBottom: '4px' }}>
                  🌦️ Climate & Conservation Scenario Sensitivity
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                  Click any scenario below to view its projected trajectory on the dashboard.
                </p>

                <div className="scenario-comparison-grid">
                  {Object.entries(prediction.all_scenarios_comparison || {}).map(([key, s]) => {
                    const isActive = selectedScenario === key;
                    const diffSign = s.depth_change_m >= 0 ? '+' : '';
                    const isDeeper = s.depth_change_m > 0;
                    return (
                      <div
                        key={key}
                        className={`scenario-card ${isActive ? 'active-scenario' : ''}`}
                        onClick={() => handleScenarioChange(key)}
                      >
                        <div className="scenario-card-header">
                          <span>{s.icon}</span>
                          <span>{s.name}</span>
                        </div>
                        <div className="scenario-card-depth">
                          {s.final_year_depth_m_bgl?.toFixed(2)} <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>m bgl</span>
                        </div>
                        <div className={`scenario-card-diff ${isDeeper ? 'deeper' : 'shallower'}`}>
                          Shift: {diffSign}{s.depth_change_m?.toFixed(2)} m ({prediction.projected_series?.slice(-1)[0]?.year})
                        </div>
                        <div className="scenario-card-footer">
                          <span>SOE: {s.final_year_soe_percent?.toFixed(1)}%</span>
                          <span className={`badge badge-${s.final_year_category?.toLowerCase() || 'safe'}`} style={{ fontSize: '0.72rem', padding: '2px 8px' }}>
                            {s.final_year_category}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>

              {/* Key Findings & AI Hydro-Statistical Insights */}
              <section className="card" style={{ marginBottom: '24px' }}>
                <h3 className="card-title" style={{ marginBottom: '16px' }}>
                  💡 Hydro-Statistical Findings & Advisory
                </h3>
                <div className="prediction-insights-list">
                  {prediction.insights?.map((item, idx) => (
                    <div key={idx} className={`prediction-insight-item ${item.type}`}>
                      <div className="prediction-insight-icon">
                        {item.type === 'alert' ? '⚠️' : item.type === 'recommendation' ? '💧' : '📊'}
                      </div>
                      <div className="prediction-insight-body">
                        <div className="prediction-insight-title">{item.title}</div>
                        <p className="prediction-insight-text">{item.content}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="methodology-banner">
                  <strong>Model Methodology:</strong> {prediction.methodology?.label} · Powered by Central Ground Water Board (CGWB) observation well datasets (1994–2026).<br />
                  <em>{prediction.methodology?.disclaimer}</em>
                </div>
              </section>
            </>
          )}
        </>
      )}

      {/* ───────────────────────────────────────────────────────────── */}
      {/* TAB 2: LIVE WEATHER & 7-DAY IMPACT (Open-Meteo)               */}
      {/* ───────────────────────────────────────────────────────────── */}
      {activeTab === 'weather' && selectedDistrict && (
        <>
          {loadingWeather && (
            <div>
              <div className="skeleton skeleton-title"></div>
              <div className="stats-grid">
                <div className="skeleton skeleton-card"></div>
                <div className="skeleton skeleton-card"></div>
                <div className="skeleton skeleton-card"></div>
              </div>
              <div className="skeleton" style={{ height: '300px', marginTop: '20px' }}></div>
            </div>
          )}

          {weatherError && <div className="alert-box alert-danger">{weatherError}</div>}

          {forecast && !loadingWeather && (
            <>
              {/* Current Weather Card */}
              <WeatherCard
                location={forecast.location || selectedDistrict}
                current={forecast.current}
                forecast={forecast.daily_forecast?.slice(0, 3)}
                updatedAt={forecast.current?.time}
              />

              {/* Groundwater Impact Panel */}
              {forecast.groundwater_impact && (
                <section className={`forecast-impact-card card ${getImpactClass(forecast.groundwater_impact.risk_level)}`}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
                    <h3 className="card-title" style={{ margin: 0, color: 'var(--text-main)' }}>
                      💧 Groundwater Recharge Impact Assessment
                    </h3>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                      <span className={`recharge-badge ${getRechargeBadgeClass(forecast.groundwater_impact.recharge_potential)}`}>
                        {forecast.groundwater_impact.recharge_potential} Recharge
                      </span>
                      <span className={`badge badge-${forecast.groundwater_impact.risk_level?.toLowerCase().replace(/[\s-]+/g, '-') || 'safe'}`} style={{ fontSize: '0.82rem', padding: '6px 14px' }}>
                        {forecast.groundwater_impact.risk_level}
                      </span>
                    </div>
                  </div>

                  {/* Narrative */}
                  <p style={{ fontSize: '0.92rem', lineHeight: '1.6', color: 'var(--text-main)', marginBottom: '16px' }}>
                    {forecast.groundwater_impact.narrative}
                  </p>

                  {/* Impact metrics row */}
                  <div className="impact-metrics-row">
                    <div className="impact-metric">
                      <div className="metric-value" style={{ color: '#0ea5e9' }}>
                        {forecast.groundwater_impact.forecast_total_rain_mm?.toFixed(1) ?? '--'} mm
                      </div>
                      <div className="metric-label">7-Day Forecast Rain</div>
                    </div>
                    <div className="impact-metric">
                      <div className="metric-value" style={{ color: 'var(--secondary-color)' }}>
                        {forecast.groundwater_impact.historical_avg_rain_mm?.toFixed(0) ?? '--'} mm
                      </div>
                      <div className="metric-label">Historical Avg Annual Rain</div>
                    </div>
                    <div className="impact-metric">
                      <div className="metric-value" style={{ color: 'var(--primary-color)' }}>
                        {forecast.groundwater_impact.rain_vs_avg_percent?.toFixed(1) ?? '--'}%
                      </div>
                      <div className="metric-label">Rain vs Annual Avg</div>
                    </div>
                    <div className="impact-metric">
                      <div className="metric-value" style={{ color: forecast.groundwater_impact.extraction_rate_percent > 70 ? 'var(--color-critical)' : 'var(--color-semi-critical)' }}>
                        {forecast.groundwater_impact.extraction_rate_percent?.toFixed(1) ?? '--'}%
                      </div>
                      <div className="metric-label">Extraction Rate</div>
                    </div>
                  </div>

                  <div style={{ marginTop: '12px', fontSize: '0.7rem', color: 'var(--text-muted)', textAlign: 'right' }}>
                    Source: {forecast.source || 'Open-Meteo + INGRES Historical Data'}
                  </div>
                </section>
              )}

              {/* 48-Hour Hourly Rainfall Timeline */}
              <section className="card" style={{ marginBottom: '24px' }}>
                <h3 className="card-title">⏱️ 48-Hour Precipitation Timeline</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '15px' }}>
                  Hourly rainfall forecast showing when precipitation is expected. Source: Open-Meteo.
                </p>
                <div className="hourly-timeline-container">
                  <ErrorBoundary>
                    <ResponsiveContainer width="100%" height={240}>
                      <BarChart data={formatHourlyData()} barCategoryGap="1%">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="shortLabel"
                          interval={5}
                          tick={{ fontSize: 10 }}
                          angle={-45}
                          textAnchor="end"
                          height={50}
                        />
                        <YAxis
                          label={{ value: 'Rain (mm)', angle: -90, position: 'insideLeft', fontSize: 11 }}
                          tick={{ fontSize: 10 }}
                        />
                        <Tooltip
                          labelFormatter={(_, payload) => payload?.[0]?.payload?.label || ''}
                          formatter={(value) => [`${value} mm`, 'Precipitation']}
                        />
                        <Bar dataKey="rain_mm" fill="#0ea5e9" name="Hourly Rain (mm)" radius={[2, 2, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </ErrorBoundary>
                </div>
              </section>

              {/* 7-Day Forecast Grid */}
              <section className="card" style={{ marginBottom: '24px' }}>
                <h3 className="card-title">📅 7-Day Weather Forecast</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '15px' }}>
                  Daily temperature, precipitation, and conditions for the week ahead. Source: Open-Meteo.
                </p>
                <div className="forecast-day-grid">
                  {forecast.daily_forecast?.map((day, idx) => {
                    const dayIcon = weatherIconMap[day.weather_code] || 'wi-day-sunny';
                    const dateLabel = day.date
                      ? new Date(day.date).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })
                      : `Day ${idx + 1}`;
                    return (
                      <div key={idx} className="forecast-day-card">
                        <div className="day-label">{dateLabel}</div>
                        <i className={`wi ${dayIcon} day-icon`} />
                        <div className="day-temp">
                          {day.temp_max != null ? `${day.temp_max.toFixed(0)}°` : '--'} / {day.temp_min != null ? `${day.temp_min.toFixed(0)}°C` : '--'}
                        </div>
                        <div className="day-detail">{day.description}</div>
                        {day.precipitation_sum != null && (
                          <div className="day-rain">🌧️ {day.precipitation_sum.toFixed(1)} mm</div>
                        )}
                        {day.precipitation_probability != null && (
                          <div className="day-detail">💧 {day.precipitation_probability}% chance</div>
                        )}
                        {day.humidity != null && (
                          <div className="day-detail">Humidity: {day.humidity.toFixed(0)}%</div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </section>

              {/* Rainfall vs Soil Moisture */}
              <section className="data-grid-2">
                <div className="card">
                  <h3 className="card-title">🌧️ Daily Rainfall Forecast</h3>
                  <div style={{ minHeight: '250px' }}>
                    <ErrorBoundary>
                      <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={formatSoilData()}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                          <YAxis label={{ value: 'Rain (mm)', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                          <Tooltip />
                          <Bar dataKey="rain" fill="#0ea5e9" name="Rain (mm)" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </ErrorBoundary>
                  </div>
                </div>

                <div className="card">
                  <h3 className="card-title">🌱 Soil Moisture & Evapotranspiration</h3>
                  <div className="soil-moisture-section">
                    <ErrorBoundary>
                      <ResponsiveContainer width="100%" height={250}>
                        <LineChart data={formatSoilData()}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                          <YAxis yAxisId="left" label={{ value: 'Soil Moisture (%)', angle: -90, position: 'insideLeft', fontSize: 10 }} />
                          <YAxis yAxisId="right" orientation="right" label={{ value: 'ET₀ (mm)', angle: 90, position: 'insideRight', fontSize: 10 }} />
                          <Tooltip />
                          <Legend />
                          <Line yAxisId="left" type="monotone" dataKey="soil_moisture" stroke="#2e7d32" strokeWidth={2} name="Soil Moisture (%)" dot={{ r: 4 }} />
                          <Line yAxisId="right" type="monotone" dataKey="et0" stroke="#f57c00" strokeWidth={2} name="ET₀ (mm)" dot={{ r: 4 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </ErrorBoundary>
                  </div>
                </div>
              </section>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default Forecast;
