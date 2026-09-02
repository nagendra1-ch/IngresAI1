import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import api from '../services/api';
import '../styles/main.css';
import '../styles/gismap.css';

const GisMap = () => {
  const mapRef = useRef(null);
  const mapContainerRef = useRef(null);
  const tileLayerRef = useRef(null);
  const markersGroupRef = useRef(null);
  const heatLayerRef = useRef(null);
  const navigate = useNavigate();

  const [districts, setDistricts] = useState([]);
  const [filteredDistricts, setFilteredDistricts] = useState([]);
  const [states, setStates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Multi-map settings
  const [baseLayer, setBaseLayer] = useState('street'); // 'street' | 'satellite' | 'landscape'
  const [metricMode, setMetricMode] = useState('groundwater'); // 'groundwater' | 'heatmap' | 'rainfall' | 'weather'
  const [weatherData, setWeatherData] = useState({});
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [heatPluginLoaded, setHeatPluginLoaded] = useState(false);

  // Filtering state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [selectedCategories, setSelectedCategories] = useState({
    'Safe': true,
    'Semi-Critical': true,
    'Critical': true,
    'Over-Exploited': true,
    'Saline': true,
    'Unknown': true,
  });

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Map Category Colors mapping
  const CATEGORY_COLORS = {
    'Safe': '#2e7d32',
    'Semi-Critical': '#f57c00',
    'Critical': '#d32f2f',
    'Over-Exploited': '#880e4f',
    'Saline': '#1565c0',
    'Unknown': '#757575',
  };

  // Helper to determine rainfall colors
  const getRainfallColor = (mm) => {
    if (mm === null || mm === undefined) return '#757575';
    if (mm < 150) return '#bbdefb'; // Light Blue
    if (mm < 400) return '#64b5f6';
    if (mm < 800) return '#2196f3';
    if (mm < 1200) return '#1976d2';
    return '#0d47a1'; // Deep Blue
  };

  // Helper to determine temperature colors
  const getTemperatureColor = (temp) => {
    if (temp === null || temp === undefined) return '#757575';
    if (temp < 18) return '#0288d1'; // Cool Blue
    if (temp < 25) return '#4caf50'; // Mild Green
    if (temp < 32) return '#ff9800'; // Warm Orange
    return '#f44336'; // Hot Red
  };

  // Load Leaflet.heat plugin dynamically from CDN
  useEffect(() => {
    if (window.L && window.L.heatLayer) {
      setHeatPluginLoaded(true);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js';
    script.async = true;
    script.onload = () => setHeatPluginLoaded(true);
    document.body.appendChild(script);

    return () => {
      // Clean up script reference if needed
    };
  }, []);

  // Fetch districts with coordinates and metrics from backend
  useEffect(() => {
    const fetchMapData = async () => {
      try {
        setLoading(true);
        const res = await api.get('/api/districts/map');
        setDistricts(res.data);
        setFilteredDistricts(res.data);

        // Extract unique states
        const uniqueStates = [...new Set(res.data.map(d => d.state_name).filter(Boolean))].sort();
        setStates(uniqueStates);
        setError('');
      } catch (err) {
        console.error('Failed to fetch GIS map data:', err);
        setError('Failed to load groundwater mapping data. Please check if the server is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchMapData();
  }, []);

  // Fetch weather data when weather metric selected
  useEffect(() => {
    if (metricMode !== 'weather' || Object.keys(weatherData).length > 0 || loading || error) return;

    const fetchWeatherMapData = async () => {
      try {
        setWeatherLoading(true);
        const res = await api.get('/api/weather/map-weather');
        setWeatherData(res.data);
      } catch (err) {
        console.error('Failed to fetch live map weather:', err);
      } finally {
        setWeatherLoading(false);
      }
    };

    fetchWeatherMapData();
  }, [metricMode, loading, error]);

  // Initialize Leaflet Map
  useEffect(() => {
    if (loading || error || !mapContainerRef.current) return;

    // Create Leaflet Map instance
    const map = L.map(mapContainerRef.current, {
      center: [22.9734, 78.6569], // Central India coordinates
      zoom: 5,
      zoomControl: false,
    });

    mapRef.current = map;

    // Add customized Zoom Control
    L.control.zoom({
      position: 'bottomright'
    }).addTo(map);

    // Set initial base layer
    const isDark = false; // Forced light/white mode map theme
    let initialUrl = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
    let attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';
    
    if (isDark) {
      initialUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
    }

    tileLayerRef.current = L.tileLayer(initialUrl, {
      attribution: attr,
      subdomains: 'abcd',
      maxZoom: 20
    }).addTo(map);

    // Initialize FeatureGroup to manage district circle markers
    const markersGroup = L.featureGroup().addTo(map);
    markersGroupRef.current = markersGroup;

    // Cleanup on unmount
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [loading, error]);

  // Handle Base Layer changes dynamically
  useEffect(() => {
    if (!mapRef.current || !tileLayerRef.current) return;

    // Remove old layer
    mapRef.current.removeLayer(tileLayerRef.current);

    let url = '';
    let attr = '';
    
    if (baseLayer === 'street') {
      const isDark = false; // Forced light/white mode map theme
      url = isDark
        ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
      attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';
    } else if (baseLayer === 'satellite') {
      url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
      attr = 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community';
    } else if (baseLayer === 'landscape') {
      url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}';
      attr = 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community';
    }

    tileLayerRef.current = L.tileLayer(url, {
      attribution: attr,
      maxZoom: 19
    }).addTo(mapRef.current);
  }, [baseLayer]);

  // Handle Filtering changes (Search, State, Categories)
  useEffect(() => {
    let result = districts;

    // Filter by Search Query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(d => 
        d.district_name.toLowerCase().includes(q) || 
        d.state_name.toLowerCase().includes(q)
      );
    }

    // Filter by State
    if (selectedState) {
      result = result.filter(d => d.state_name === selectedState);
    }

    // Filter by Categories
    result = result.filter(d => {
      const cat = d.assessment_category || 'Unknown';
      let key = 'Unknown';
      if (cat.includes('Safe')) key = 'Safe';
      else if (cat.includes('Semi-Critical') || cat.includes('Semi Critical')) key = 'Semi-Critical';
      else if (cat.includes('Critical')) key = 'Critical';
      else if (cat.includes('Over-Exploited') || cat.includes('Over Exploited')) key = 'Over-Exploited';
      else if (cat.includes('Saline')) key = 'Saline';
      
      return selectedCategories[key];
    });

    setFilteredDistricts(result);
  }, [searchQuery, selectedState, selectedCategories, districts]);

  // Update Map Layers when filtered districts, metric mode or weather data changes
  useEffect(() => {
    if (!mapRef.current) return;

    // Clear old vector markers
    if (markersGroupRef.current) {
      markersGroupRef.current.clearLayers();
    }

    // Remove old heatmap layer
    if (heatLayerRef.current) {
      mapRef.current.removeLayer(heatLayerRef.current);
      heatLayerRef.current = null;
    }

    // Mode 1: Heatmap of Extraction Stage
    if (metricMode === 'heatmap') {
      if (!heatPluginLoaded || !window.L.heatLayer) return;

      const heatPoints = filteredDistricts
        .filter(d => d.latitude !== null && d.longitude !== null && d.stage_of_groundwater_extraction_percent !== null)
        .map(d => {
          // Normalize extraction stage: e.g. 100% extraction maps to 0.7 intensity
          const intensity = Math.min(1.0, Math.max(0.1, d.stage_of_groundwater_extraction_percent / 130.0));
          return [d.latitude, d.longitude, intensity];
        });

      heatLayerRef.current = window.L.heatLayer(heatPoints, {
        radius: 28,
        blur: 18,
        maxZoom: 7,
        gradient: { 0.2: 'blue', 0.4: 'green', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red' }
      }).addTo(mapRef.current);
      
      return;
    }

    // Mode 2, 3, 4: Vector circle markers (Groundwater, Rainfall, Weather)
    filteredDistricts.forEach(d => {
      if (d.latitude === null || d.longitude === null) return;

      let fillColor = '#757575';
      let radius = 8;
      let titleContent = '';
      let tableRows = '';

      if (metricMode === 'groundwater') {
        const cat = d.assessment_category || 'Unknown';
        let colorKey = 'Unknown';
        if (cat.includes('Safe')) colorKey = 'Safe';
        else if (cat.includes('Semi-Critical') || cat.includes('Semi Critical')) colorKey = 'Semi-Critical';
        else if (cat.includes('Critical')) colorKey = 'Critical';
        else if (cat.includes('Over-Exploited') || cat.includes('Over Exploited')) colorKey = 'Over-Exploited';
        else if (cat.includes('Saline')) colorKey = 'Saline';

        fillColor = CATEGORY_COLORS[colorKey];
        radius = 8;
        titleContent = `
          <span class="badge" style="background-color: ${fillColor}; color: white; padding: 2px 6px; font-size: 10px; border-radius: 4px;">
            ${d.assessment_category || 'Not Assessed'}
          </span>
        `;
        tableRows = `
          <tr>
            <td>Category:</td>
            <td style="color: ${fillColor}; font-weight: bold;">${d.assessment_category || 'N/A'}</td>
          </tr>
          <tr>
            <td>Water Level Depth:</td>
            <td><strong>${d.depth_to_water_level_m_bgl !== null ? `${d.depth_to_water_level_m_bgl.toFixed(2)} m bgl` : 'N/A'}</strong></td>
          </tr>
          <tr>
            <td>Extraction Stage:</td>
            <td><strong>${d.stage_of_groundwater_extraction_percent !== null ? `${d.stage_of_groundwater_extraction_percent.toFixed(1)}%` : 'N/A'}</strong></td>
          </tr>
        `;
      } 
      else if (metricMode === 'rainfall') {
        fillColor = getRainfallColor(d.rainfall_mm);
        // Sizing proportional to rainfall
        radius = d.rainfall_mm !== null ? Math.max(5, Math.min(22, d.rainfall_mm / 70)) : 6;
        titleContent = `
          <span class="badge" style="background-color: ${fillColor}; color: white; padding: 2px 6px; font-size: 10px; border-radius: 4px;">
            Rainfall: ${d.rainfall_mm !== null ? `${d.rainfall_mm.toFixed(1)} mm` : 'No Data'}
          </span>
        `;
        tableRows = `
          <tr>
            <td>Annual Rainfall:</td>
            <td style="color: ${fillColor}; font-weight: bold;">${d.rainfall_mm !== null ? `${d.rainfall_mm.toFixed(1)} mm` : 'N/A'}</td>
          </tr>
          <tr>
            <td>Water Level Depth:</td>
            <td>${d.depth_to_water_level_m_bgl !== null ? `${d.depth_to_water_level_m_bgl.toFixed(2)} m bgl` : 'N/A'}</td>
          </tr>
        `;
      } 
      else if (metricMode === 'weather') {
        const w = weatherData[d.id];
        const temp = w ? w.temp : null;
        const humidity = w ? w.humidity : null;
        fillColor = getTemperatureColor(temp);
        radius = 8;
        titleContent = `
          <span class="badge" style="background-color: ${fillColor}; color: white; padding: 2px 6px; font-size: 10px; border-radius: 4px;">
            Live Temp: ${temp !== null ? `${temp}°C` : 'Fetching...'}
          </span>
        `;
        tableRows = `
          <tr>
            <td>Live Temperature:</td>
            <td style="color: ${fillColor}; font-weight: bold;">${temp !== null ? `${temp} °C` : 'N/A'}</td>
          </tr>
          <tr>
            <td>Relative Humidity:</td>
            <td>${humidity !== null ? `${humidity}%` : 'N/A'}</td>
          </tr>
          <tr>
            <td>Annual Rainfall:</td>
            <td>${d.rainfall_mm !== null ? `${d.rainfall_mm.toFixed(1)} mm` : 'N/A'}</td>
          </tr>
        `;
      }

      // Create vector marker
      const marker = L.circleMarker([d.latitude, d.longitude], {
        radius: radius,
        fillColor: fillColor,
        color: '#ffffff',
        weight: 1.5,
        opacity: 0.95,
        fillOpacity: 0.85,
      });

      // Tooltip
      marker.bindTooltip(`
        <div class="gis-tooltip">
          <strong>${d.district_name}</strong> (${d.state_name})<br/>
          ${titleContent}
        </div>
      `, {
        direction: 'top',
        offset: [0, -5],
        opacity: 0.9,
      });

      // Popup content
      const popupContent = document.createElement('div');
      popupContent.className = 'gis-popup-container';
      popupContent.innerHTML = `
        <div class="gis-popup-header" style="border-bottom: 2px solid ${fillColor};">
          <h4>${d.district_name}</h4>
          <span class="gis-popup-state">${d.state_name}</span>
        </div>
        <div class="gis-popup-body">
          <table class="gis-popup-table">
            <tbody>
              ${tableRows}
              <tr>
                <td>Annual Recharge:</td>
                <td>${d.annual_groundwater_recharge_ham !== null ? `${d.annual_groundwater_recharge_ham.toLocaleString()} ham` : 'N/A'}</td>
              </tr>
            </tbody>
          </table>
          <button class="btn btn-primary btn-block gis-popup-btn">View Full Details</button>
        </div>
      `;

      // Navigate detailed page
      const btn = popupContent.querySelector('.gis-popup-btn');
      if (btn) {
        btn.addEventListener('click', () => {
          navigate(`/districts/${d.id}`);
        });
      }

      marker.bindPopup(popupContent, {
        maxWidth: 280,
        className: 'custom-gis-popup',
      });

      if (markersGroupRef.current) {
        markersGroupRef.current.addLayer(marker);
      }
    });

    // Auto zoom map to selected search district
    if (filteredDistricts.length > 0 && searchQuery.trim() && mapRef.current && markersGroupRef.current) {
      try {
        const bounds = markersGroupRef.current.getBounds();
        if (bounds.isValid()) {
          mapRef.current.fitBounds(bounds, { maxZoom: 9, padding: [30, 30] });
        }
      } catch (e) {
        console.warn('Could not fit bounds:', e);
      }
    }
  }, [filteredDistricts, metricMode, weatherData, heatPluginLoaded]);

  // Navigate & zoom map to a specific selected district from results list
  const handleZoomToDistrict = (d) => {
    if (!mapRef.current) return;
    mapRef.current.setView([d.latitude, d.longitude], 9);
    
    if (markersGroupRef.current) {
      markersGroupRef.current.eachLayer(layer => {
        const latlng = layer.getLatLng();
        if (latlng.lat === d.latitude && latlng.lng === d.longitude) {
          layer.openPopup();
        }
      });
    }
  };

  const handleCategoryCheckboxChange = (key) => {
    setSelectedCategories(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const resetFilters = () => {
    setSearchQuery('');
    setSelectedState('');
    setSelectedCategories({
      'Safe': true,
      'Semi-Critical': true,
      'Critical': true,
      'Over-Exploited': true,
      'Saline': true,
      'Unknown': true,
    });
  };

  return (
    <div className="gis-layout">
      {/* Sidebar Controls Overlay */}
      <div className={`gis-sidebar ${isSidebarOpen ? '' : 'collapsed'}`}>
        <button 
          className="gis-sidebar-toggle" 
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          title={isSidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
        >
          {isSidebarOpen ? '◀' : '▶'}
        </button>

        <div className="gis-sidebar-content">
          <div className="gis-header">
            <h3>🌐 GIS Explorer</h3>
            <p className="subtitle">Groundwater Intelligence Map</p>
          </div>

          {/* Metric Selector Tabs */}
          <div className="gis-control-group">
            <label>Overlay Parameter</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', margin: '4px 0 10px 0' }}>
              <button 
                className={`btn btn-sm ${metricMode === 'groundwater' ? 'btn-primary' : 'btn-outline'}`}
                style={{ fontSize: '11px', padding: '6px 4px' }}
                onClick={() => setMetricMode('groundwater')}
              >
                💧 Categories
              </button>
              <button 
                className={`btn btn-sm ${metricMode === 'heatmap' ? 'btn-primary' : 'btn-outline'}`}
                style={{ fontSize: '11px', padding: '6px 4px' }}
                onClick={() => setMetricMode('heatmap')}
              >
                🔥 Thermal (GW)
              </button>
              <button 
                className={`btn btn-sm ${metricMode === 'rainfall' ? 'btn-primary' : 'btn-outline'}`}
                style={{ fontSize: '11px', padding: '6px 4px' }}
                onClick={() => setMetricMode('rainfall')}
              >
                🌧️ Rainfall
              </button>
              <button 
                className={`btn btn-sm ${metricMode === 'weather' ? 'btn-primary' : 'btn-outline'}`}
                style={{ fontSize: '11px', padding: '6px 4px' }}
                onClick={() => setMetricMode('weather')}
              >
                ☀️ Live Weather
              </button>
            </div>
          </div>

          <div className="gis-control-group">
            <label htmlFor="gis-search">Search District</label>
            <div className="gis-search-wrapper">
              <input 
                id="gis-search"
                type="text" 
                placeholder="Type name (e.g. Guntur)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button className="clear-btn" onClick={() => setSearchQuery('')}>×</button>
              )}
            </div>
          </div>

          <div className="gis-control-group">
            <label htmlFor="gis-state-filter">Filter by State</label>
            <select
              id="gis-state-filter"
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
            >
              <option value="">All States</option>
              {states.map(st => (
                <option key={st} value={st}>{st}</option>
              ))}
            </select>
          </div>

          {/* Render category checkboxes only for groundwater & heatmap modes */}
          {(metricMode === 'groundwater' || metricMode === 'heatmap') && (
            <div className="gis-control-group">
              <label>Assessment Category</label>
              <div className="gis-checkbox-list">
                {Object.keys(CATEGORY_COLORS).map(cat => (
                  <label key={cat} className="gis-checkbox-label">
                    <input
                      type="checkbox"
                      checked={selectedCategories[cat]}
                      onChange={() => handleCategoryCheckboxChange(cat)}
                    />
                    <span className="checkbox-color-box" style={{ backgroundColor: CATEGORY_COLORS[cat] }}></span>
                    <span className="checkbox-text">{cat}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="gis-action-buttons">
            <button className="btn btn-outline btn-block" onClick={resetFilters}>
              Reset Filters
            </button>
          </div>

          <div className="gis-stats-summary">
            <div className="gis-stat-card">
              <span className="stat-label">Displayed Districts</span>
              <span className="stat-value">{filteredDistricts.length}</span>
              <span className="stat-total">out of {districts.length} total</span>
            </div>
          </div>

          {/* Quick results selection */}
          {searchQuery && filteredDistricts.length > 0 && (
            <div className="gis-quick-results">
              <h4>Quick Results ({filteredDistricts.length})</h4>
              <ul className="quick-results-list">
                {filteredDistricts.slice(0, 15).map(d => {
                  let bulletBg = CATEGORY_COLORS[d.assessment_category] || CATEGORY_COLORS.Unknown;
                  if (metricMode === 'rainfall') bulletBg = getRainfallColor(d.rainfall_mm);
                  if (metricMode === 'weather') bulletBg = getTemperatureColor(weatherData[d.id]?.temp);
                  if (metricMode === 'heatmap') bulletBg = '#d32f2f';

                  return (
                    <li key={d.id} onClick={() => handleZoomToDistrict(d)}>
                      <span className="bullet" style={{ backgroundColor: bulletBg }}></span>
                      <div className="result-info">
                        <span className="result-name">{d.district_name}</span>
                        <span className="result-state">{d.state_name}</span>
                      </div>
                    </li>
                  );
                })}
                {filteredDistricts.length > 15 && <li className="more-indicator">...and {filteredDistricts.length - 15} more</li>}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Fullscreen Map container */}
      <div className="gis-map-wrapper">
        {(loading || (metricMode === 'weather' && weatherLoading)) && (
          <div className="gis-map-loader">
            <div className="loader-spinner"></div>
            <p>{loading ? 'Loading Groundwater GIS layers...' : 'Syncing Live Temperature Overlays...'}</p>
          </div>
        )}
        
        {error && (
          <div className="gis-map-error">
            <span className="error-icon">⚠️</span>
            <p>{error}</p>
          </div>
        )}

        {/* Floating Base Map Toggles (Top-Right) */}
        <div style={{ position: 'absolute', top: '20px', right: '20px', zIndex: 1000, display: 'flex', gap: '6px', background: 'var(--surface-color)', padding: '6px', borderRadius: 'var(--border-radius-md)', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-md)' }}>
          <button 
            className={`btn btn-sm ${baseLayer === 'street' ? 'btn-primary' : 'btn-outline'}`}
            style={{ fontSize: '11px', padding: '6px 10px', height: '30px' }}
            onClick={() => setBaseLayer('street')}
          >
            🗺️ Streets
          </button>
          <button 
            className={`btn btn-sm ${baseLayer === 'satellite' ? 'btn-primary' : 'btn-outline'}`}
            style={{ fontSize: '11px', padding: '6px 10px', height: '30px' }}
            onClick={() => setBaseLayer('satellite')}
          >
            🛰️ Satellite
          </button>
          <button 
            className={`btn btn-sm ${baseLayer === 'landscape' ? 'btn-primary' : 'btn-outline'}`}
            style={{ fontSize: '11px', padding: '6px 10px', height: '30px' }}
            onClick={() => setBaseLayer('landscape')}
          >
            ⛰️ Terrain
          </button>
        </div>

        <div className="gis-map-container" ref={mapContainerRef}></div>

        {/* Floating Map Legend Overlay (Dynamic based on selected parameter) */}
        <div className="gis-floating-legend">
          {metricMode === 'groundwater' && (
            <>
              <h4>GWRA Category</h4>
              <div className="legend-items">
                {Object.keys(CATEGORY_COLORS).map(cat => (
                  <div key={cat} className="legend-item">
                    <span className="legend-color-dot" style={{ backgroundColor: CATEGORY_COLORS[cat] }}></span>
                    <span className="legend-label">{cat}</span>
                  </div>
                ))}
              </div>
            </>
          )}

          {metricMode === 'heatmap' && (
            <>
              <h4>Extraction Intensity</h4>
              <div className="legend-items">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '100%' }}>
                  <div style={{ height: '12px', width: '100%', background: 'linear-gradient(to right, blue, green, yellow, orange, red)', borderRadius: '3px' }}></div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)' }}>
                    <span>Safe (&lt;40%)</span>
                    <span style={{ marginLeft: 'auto' }}>Over-Exploited (&gt;100%)</span>
                  </div>
                </div>
              </div>
            </>
          )}

          {metricMode === 'rainfall' && (
            <>
              <h4>Annual Rainfall</h4>
              <div className="legend-items">
                <div className="legend-item"><span className="legend-color-dot" style={{ backgroundColor: '#bbdefb' }}></span><span className="legend-label">&lt; 150 mm</span></div>
                <div className="legend-item"><span className="legend-color-dot" style={{ backgroundColor: '#64b5f6' }}></span><span className="legend-label">150 - 400 mm</span></div>
                <div className="legend-item"><span className="legend-color-dot" style={{ backgroundColor: '#2196f3' }}></span><span className="legend-label">400 - 800 mm</span></div>
                <div className="legend-item"><span className="legend-color-dot" style={{ backgroundColor: '#1976d2' }}></span><span className="legend-label">800 - 1200 mm</span></div>
                <div className="legend-item"><span className="legend-color-dot" style={{ backgroundColor: '#0d47a1' }}></span><span className="legend-label">&gt; 1200 mm</span></div>
              </div>
            </>
          )}

          {metricMode === 'weather' && (
            <>
              <h4>Live Temperature</h4>
              <div className="legend-items">
                <div className="legend-item"><span className="legend-color-dot" style={{ backgroundColor: '#0288d1' }}></span><span className="legend-label">Cool (&lt; 18°C)</span></div>
                <div className="legend-item"><span className="legend-color-dot" style={{ backgroundColor: '#4caf50' }}></span><span className="legend-label">Mild (18 - 25°C)</span></div>
                <div className="legend-item"><span className="legend-color-dot" style={{ backgroundColor: '#ff9800' }}></span><span className="legend-label">Warm (25 - 32°C)</span></div>
                <div className="legend-item"><span className="legend-color-dot" style={{ backgroundColor: '#f44336' }}></span><span className="legend-label">Hot (&gt; 32°C)</span></div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default GisMap;
