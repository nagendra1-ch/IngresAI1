import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import '../styles/main.css';

const AdminDashboard = () => {
  const { user: currentUser } = useAuth();
  const navigate = useNavigate();

  // Active Tab: 'overview' | 'users' | 'data-editor'
  const [activeTab, setActiveTab] = useState('overview');

  // Loading and alerts
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');
  const [toastMessage, setToastMessage] = useState(null);

  // Tab 1: Overview & Telemetry Data
  const [stats, setStats] = useState(null);
  const [queryLogs, setQueryLogs] = useState([]);
  const [accessStats, setAccessStats] = useState([]);

  // Tab 2: User Management Data
  const [userLogs, setUserLogs] = useState([]);
  const [userSearch, setUserSearch] = useState('');
  const [resetModalUser, setResetModalUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [deleteModalUser, setDeleteModalUser] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Tab 3: Data Editor Data
  const [dataRecords, setDataRecords] = useState([]);
  const [dataTotal, setDataTotal] = useState(0);
  const [dataPage, setDataPage] = useState(1);
  const [dataPageSize] = useState(15);
  const [dataSearch, setDataSearch] = useState('');
  const [dataCategoryFilter, setDataCategoryFilter] = useState('all');
  const [dataYearFilter, setDataYearFilter] = useState('');
  const [editingRecord, setEditingRecord] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const [dataLoading, setDataLoading] = useState(false);

  const showToast = (text, type = 'success') => {
    setToastMessage({ text, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Fetch Overview Data
  const fetchOverviewData = async () => {
    try {
      setLoading(true);
      const [statsRes, usersRes, queriesRes, accessRes] = await Promise.all([
        api.get('/api/admin/statistics'),
        api.get('/api/admin/users'),
        api.get('/api/admin/queries'),
        api.get('/api/admin/access-statistics')
      ]);
      setStats(statsRes.data);
      setUserLogs(usersRes.data);
      setQueryLogs(queriesRes.data);
      setAccessStats(accessRes.data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load admin data", err);
      setError("Forbidden: Access restricted to administrators only.");
      setLoading(false);
    }
  };

  // Fetch Data Editor Records
  const fetchDataEditorRecords = async (page = 1) => {
    try {
      setDataLoading(true);
      const params = {
        page,
        page_size: dataPageSize,
      };
      if (dataSearch.trim()) params.search = dataSearch.trim();
      if (dataCategoryFilter !== 'all') params.category = dataCategoryFilter;
      if (dataYearFilter) params.year = parseInt(dataYearFilter);

      const res = await api.get('/api/admin/data-editor/records', { params });
      setDataRecords(res.data.records);
      setDataTotal(res.data.total);
      setDataPage(res.data.page);
      setDataLoading(false);
    } catch (err) {
      console.error("Failed to load data editor records", err);
      setDataLoading(false);
    }
  };

  useEffect(() => {
    fetchOverviewData();
  }, []);

  useEffect(() => {
    if (activeTab === 'data-editor') {
      fetchDataEditorRecords(1);
    }
  }, [activeTab, dataSearch, dataCategoryFilter, dataYearFilter]);

  // Export Excel
  const handleExportExcel = async () => {
    try {
      setExporting(true);
      const response = await api.get('/api/admin/export-excel', {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'ingres_ai_admin_report.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      setExporting(false);
      showToast("Excel report downloaded successfully!");
    } catch (err) {
      console.error("Export Excel failed", err);
      showToast("Failed to export Excel report.", "danger");
      setExporting(false);
    }
  };

  // User Actions: Role Toggle
  const handleRoleToggle = async (targetUser) => {
    const newRole = targetUser.role === 'ADMIN' ? 'USER' : 'ADMIN';
    const confirmMsg = `Are you sure you want to change ${targetUser.name}'s role to ${newRole}?`;
    if (!window.confirm(confirmMsg)) return;

    try {
      setActionLoading(true);
      await api.patch(`/api/admin/users/${targetUser.id}/role`, { role: newRole });
      setUserLogs(prev => prev.map(u => u.id === targetUser.id ? { ...u, role: newRole } : u));
      showToast(`User ${targetUser.email} is now an ${newRole}.`);
      setActionLoading(false);
    } catch (err) {
      const msg = err.response?.data?.detail || "Failed to update role.";
      showToast(msg, 'danger');
      setActionLoading(false);
    }
  };

  // User Actions: Reset Password
  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (!resetModalUser || !newPassword || newPassword.length < 4) {
      showToast("Password must be at least 4 characters.", "danger");
      return;
    }

    try {
      setActionLoading(true);
      await api.post(`/api/admin/users/${resetModalUser.id}/reset-password`, { new_password: newPassword });
      showToast(`Password for ${resetModalUser.email} has been reset successfully.`);
      setResetModalUser(null);
      setNewPassword('');
      setActionLoading(false);
    } catch (err) {
      const msg = err.response?.data?.detail || "Failed to reset password.";
      showToast(msg, 'danger');
      setActionLoading(false);
    }
  };

  // User Actions: Delete User
  const handleDeleteUser = async () => {
    if (!deleteModalUser) return;
    try {
      setActionLoading(true);
      await api.delete(`/api/admin/users/${deleteModalUser.id}`);
      setUserLogs(prev => prev.filter(u => u.id !== deleteModalUser.id));
      showToast(`User ${deleteModalUser.email} has been deleted.`);
      setDeleteModalUser(null);
      setActionLoading(false);
    } catch (err) {
      const msg = err.response?.data?.detail || "Failed to delete user.";
      showToast(msg, 'danger');
      setActionLoading(false);
    }
  };

  // Data Editor: Open Edit Modal
  const handleOpenEdit = (rec) => {
    setEditingRecord(rec);
    setEditFormData({
      annual_groundwater_recharge_ham: rec.annual_groundwater_recharge_ham || '',
      annual_extractable_groundwater_resource_ham: rec.annual_extractable_groundwater_resource_ham || '',
      annual_groundwater_extraction_ham: rec.annual_groundwater_extraction_ham || '',
      stage_of_groundwater_extraction_percent: rec.stage_of_groundwater_extraction_percent || '',
      district_assessment_category: rec.district_assessment_category || 'Safe',
      rainfall_mm: rec.rainfall_mm || '',
      depth_to_water_level_m_bgl: rec.depth_to_water_level_m_bgl || ''
    });
  };

  // Data Editor: Recalculate Stage & Category on Form Input
  const handleEditInputChange = (field, value) => {
    const updated = { ...editFormData, [field]: value };

    // Auto calculate stage % if extraction and extractable are valid numbers
    if (field === 'annual_groundwater_extraction_ham' || field === 'annual_extractable_groundwater_resource_ham') {
      const ext = parseFloat(field === 'annual_groundwater_extraction_ham' ? value : updated.annual_groundwater_extraction_ham);
      const res = parseFloat(field === 'annual_extractable_groundwater_resource_ham' ? value : updated.annual_extractable_groundwater_resource_ham);
      if (!isNaN(ext) && !isNaN(res) && res > 0) {
        const stage = Number(((ext / res) * 100).toFixed(2));
        updated.stage_of_groundwater_extraction_percent = stage;
        if (stage <= 70) updated.district_assessment_category = 'Safe';
        else if (stage <= 90) updated.district_assessment_category = 'Semi-Critical';
        else if (stage <= 100) updated.district_assessment_category = 'Critical';
        else updated.district_assessment_category = 'Over-Exploited';
      }
    }

    setEditFormData(updated);
  };

  // Data Editor: Save Record
  const handleSaveRecord = async (e) => {
    e.preventDefault();
    if (!editingRecord) return;

    try {
      setActionLoading(true);
      const payload = {
        annual_groundwater_recharge_ham: editFormData.annual_groundwater_recharge_ham !== '' ? parseFloat(editFormData.annual_groundwater_recharge_ham) : null,
        annual_extractable_groundwater_resource_ham: editFormData.annual_extractable_groundwater_resource_ham !== '' ? parseFloat(editFormData.annual_extractable_groundwater_resource_ham) : null,
        annual_groundwater_extraction_ham: editFormData.annual_groundwater_extraction_ham !== '' ? parseFloat(editFormData.annual_groundwater_extraction_ham) : null,
        stage_of_groundwater_extraction_percent: editFormData.stage_of_groundwater_extraction_percent !== '' ? parseFloat(editFormData.stage_of_groundwater_extraction_percent) : null,
        district_assessment_category: editFormData.district_assessment_category,
        rainfall_mm: editFormData.rainfall_mm !== '' ? parseFloat(editFormData.rainfall_mm) : null,
        depth_to_water_level_m_bgl: editFormData.depth_to_water_level_m_bgl !== '' ? parseFloat(editFormData.depth_to_water_level_m_bgl) : null,
      };

      const res = await api.put(`/api/admin/data-editor/records/${editingRecord.id}`, payload);
      
      // Update local state list
      setDataRecords(prev => prev.map(r => r.id === editingRecord.id ? res.data : r));
      showToast(`Record for ${editingRecord.district_name} (${editingRecord.assessment_year}) updated successfully!`);
      setEditingRecord(null);
      setActionLoading(false);
    } catch (err) {
      console.error("Save failed", err);
      const msg = err.response?.data?.detail || "Failed to update record.";
      showToast(msg, 'danger');
      setActionLoading(false);
    }
  };

  const getFormatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const d = new Date(dateString);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getBadgeClass = (category) => {
    switch (category?.toLowerCase()) {
      case 'safe': return 'badge-safe';
      case 'semi-critical': return 'badge-semi-critical';
      case 'critical': return 'badge-critical';
      case 'over-exploited': return 'badge-over-exploited';
      default: return 'badge-safe';
    }
  };

  // Filtered Users
  const filteredUsers = userLogs.filter(u => 
    u.name?.toLowerCase().includes(userSearch.toLowerCase()) || 
    u.email?.toLowerCase().includes(userSearch.toLowerCase()) ||
    u.role?.toLowerCase().includes(userSearch.toLowerCase())
  );

  if (loading) {
    return (
      <div className="container-inner">
        <div className="skeleton skeleton-title"></div>
        <div className="stats-grid">
          <div className="skeleton skeleton-card"></div>
          <div className="skeleton skeleton-card"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container-inner">
        <div className="alert-box alert-danger">{error}</div>
      </div>
    );
  }

  return (
    <div className="container-inner">
      {/* Toast Alert */}
      {toastMessage && (
        <div 
          className={`alert-box ${toastMessage.type === 'danger' ? 'alert-danger' : 'alert-success'}`}
          style={{ position: 'sticky', top: '10px', zIndex: 100, marginBottom: '20px' }}
        >
          {toastMessage.text}
        </div>
      )}

      {/* Header */}
      <header className="page-header">
        <div>
          <h1 className="page-title">Admin Management Portal</h1>
          <p className="page-subtitle">Oversee users, inspect AI telemetry, edit groundwater statistics, and export reports.</p>
        </div>
        <button 
          className="btn btn-secondary" 
          onClick={handleExportExcel}
          disabled={exporting}
          style={{ padding: '10px 20px', display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          {exporting ? 'Generating Excel...' : 'Export All Data (.xlsx) 📥'}
        </button>
      </header>

      {/* Tabs Navigation */}
      <nav className="admin-tabs-nav">
        <button 
          className={`admin-tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 System Overview & Logs
        </button>
        <button 
          className={`admin-tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          👥 User Management ({userLogs.length})
        </button>
        <button 
          className={`admin-tab ${activeTab === 'data-editor' ? 'active' : ''}`}
          onClick={() => setActiveTab('data-editor')}
        >
          ✍️ Groundwater Data Editor
        </button>
      </nav>

      {/* =====================================================================
          TAB 1: SYSTEM OVERVIEW & TELEMETRY
          ===================================================================== */}
      {activeTab === 'overview' && (
        <div>
          {/* Summary Cards */}
          <section className="stats-grid">
            <div className="card">
              <div className="metric-label">Total Registered Users</div>
              <div className="metric-value">{stats?.total_users}</div>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Registered accounts</span>
            </div>

            <div className="card">
              <div className="metric-label">Total AI Queries Processed</div>
              <div className="metric-value">{stats?.total_queries}</div>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Conversations handled</span>
            </div>

            <div className="card">
              <div className="metric-label">Districts Looked Up</div>
              <div className="metric-value">{stats?.districts_accessed}</div>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Unique districts accessed</span>
            </div>

            <div className="card">
              <div className="metric-label">Most Viewed District</div>
              <div className="metric-value" style={{ fontSize: '1.7rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {stats?.most_viewed_district || 'None'}
              </div>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Total Views: {stats?.most_viewed_district_views || 0}
              </span>
            </div>
          </section>

          {/* District Access Statistics */}
          <section className="card" style={{ marginBottom: '25px' }}>
            <h3 className="card-title">🔍 District Access & Search Popularity</h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '15px' }}>
              Tracks which aquifers and districts are queried most frequently across India.
            </p>
            <div className="table-wrapper" style={{ maxHeight: '320px', overflowY: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>District</th>
                    <th>State</th>
                    <th>Total Views</th>
                    <th>Unique Analysts</th>
                  </tr>
                </thead>
                <tbody>
                  {accessStats.map((item, idx) => (
                    <tr key={idx}>
                      <td><strong>{item.district_name}</strong></td>
                      <td>{item.state_name}</td>
                      <td><span className="badge badge-safe">{item.total_views} views</span></td>
                      <td>{item.unique_users} users</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Global AI Query Activity Log */}
          <section className="card">
            <h3 className="card-title">📜 Real-Time Virtual Assistant Query Log</h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '15px' }}>
              Recent queries answered by Google Gemini AI with database grounding.
            </p>
            <div className="table-wrapper" style={{ maxHeight: '350px', overflowY: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>User</th>
                    <th>Question Asked</th>
                    <th>District</th>
                  </tr>
                </thead>
                <tbody>
                  {queryLogs.map((q) => (
                    <tr key={q.id}>
                      <td style={{ whiteSpace: 'nowrap' }}>{getFormatDate(q.created_at)}</td>
                      <td>
                        <div style={{ fontWeight: 600 }}>{q.username}</div>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{q.email}</span>
                      </td>
                      <td>
                        <div style={{ maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={q.query}>
                          {q.query}
                        </div>
                      </td>
                      <td>
                        {q.district_name !== 'N/A' ? (
                          <span className="badge badge-safe">{q.district_name}</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>General</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}

      {/* =====================================================================
          TAB 2: USER MANAGEMENT
          ===================================================================== */}
      {activeTab === 'users' && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '15px' }}>
            <div>
              <h3 className="card-title">👥 User Account Directory & Permissions</h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Manage roles, reset user passwords, and remove accounts directly.
              </p>
            </div>
            <input 
              type="text" 
              className="form-control" 
              placeholder="Search by name, email or role..." 
              value={userSearch} 
              onChange={(e) => setUserSearch(e.target.value)}
              style={{ width: '100%', maxWidth: '300px' }}
            />
          </div>

          <div className="table-wrapper">
            <table className="data-table" style={{ minWidth: '760px' }}>
              <thead>
                <tr>
                  <th>User ID</th>
                  <th>Full Name</th>
                  <th>Email Address</th>
                  <th>Role</th>
                  <th>Queries Asked</th>
                  <th>Joined Date</th>
                  <th style={{ textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((u) => {
                  const isCurrent = currentUser?.email === u.email;
                  return (
                    <tr key={u.id}>
                      <td>#{u.id}</td>
                      <td>
                        <strong>{u.name}</strong>
                        {isCurrent && <span style={{ marginLeft: '6px', fontSize: '0.75rem', color: 'var(--primary-color)' }}>(You)</span>}
                      </td>
                      <td>{u.email}</td>
                      <td>
                        <span 
                          className="badge" 
                          style={{ 
                            backgroundColor: u.role === 'ADMIN' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(14, 116, 144, 0.15)',
                            color: u.role === 'ADMIN' ? '#dc2626' : 'var(--primary-color)',
                            fontWeight: 700
                          }}
                        >
                          {u.role}
                        </span>
                      </td>
                      <td>{u.queries_count}</td>
                      <td>{new Date(u.created_at).toLocaleDateString()}</td>
                      <td style={{ textAlign: 'center' }}>
                        <div className="action-btns" style={{ justifyContent: 'center', flexWrap: 'nowrap', gap: '6px' }}>
                          {/* Role Toggle Button */}
                          <button 
                            className={`btn btn-sm ${u.role === 'ADMIN' ? 'btn-outline' : 'btn-warning'}`}
                            onClick={() => handleRoleToggle(u)}
                            disabled={isCurrent || actionLoading}
                            title={isCurrent ? "Cannot demote yourself" : (u.role === 'ADMIN' ? "Demote to Standard User" : "Promote to Admin")}
                          >
                            {u.role === 'ADMIN' ? 'Demote User' : '👑 Make Admin'}
                          </button>

                          {/* Reset Password Button */}
                          <button 
                            className="btn btn-sm btn-outline"
                            onClick={() => { setResetModalUser(u); setNewPassword(''); }}
                            disabled={actionLoading}
                            title="Reset password for this user"
                          >
                            🔑 Reset Pwd
                          </button>

                          {/* Delete User Button */}
                          <button 
                            className="btn btn-sm btn-danger"
                            onClick={() => setDeleteModalUser(u)}
                            disabled={isCurrent || actionLoading}
                            title={isCurrent ? "Cannot delete yourself" : "Delete account"}
                          >
                            🗑️ Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* =====================================================================
          TAB 3: GROUNDWATER DATA EDITOR
          ===================================================================== */}
      {activeTab === 'data-editor' && (
        <div className="card">
          <div style={{ marginBottom: '20px' }}>
            <h3 className="card-title">✍️ Pan-India Groundwater Data Editor</h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Search, view, and manually edit district groundwater recharge, extraction, rainfall, and categorization.
            </p>
          </div>

          {/* Filter Bar */}
          <div className="editor-filter-bar">
            <input 
              type="text" 
              className="form-control" 
              placeholder="Search District or State..." 
              value={dataSearch}
              onChange={(e) => setDataSearch(e.target.value)}
            />

            <select 
              className="form-control"
              value={dataCategoryFilter}
              onChange={(e) => setDataCategoryFilter(e.target.value)}
            >
              <option value="all">All Categories</option>
              <option value="Safe">Safe</option>
              <option value="Semi-Critical">Semi-Critical</option>
              <option value="Critical">Critical</option>
              <option value="Over-Exploited">Over-Exploited</option>
            </select>

            <select 
              className="form-control"
              value={dataYearFilter}
              onChange={(e) => setDataYearFilter(e.target.value)}
            >
              <option value="">All Assessment Years</option>
              <option value="2025">2025</option>
              <option value="2024">2024</option>
              <option value="2023">2023</option>
              <option value="2022">2022</option>
              <option value="2020">2020</option>
            </select>

            <button 
              className="btn btn-outline"
              onClick={() => { setDataSearch(''); setDataCategoryFilter('all'); setDataYearFilter(''); }}
            >
              Reset Filters
            </button>
          </div>

          {/* Data Table */}
          {dataLoading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>Loading district assessment records...</div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>District</th>
                    <th>State</th>
                    <th>Year</th>
                    <th>Recharge (ha-m)</th>
                    <th>Extraction (ha-m)</th>
                    <th>Stage (%)</th>
                    <th>Category</th>
                    <th>Rainfall (mm)</th>
                    <th style={{ textAlign: 'center' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {dataRecords.length === 0 ? (
                    <tr>
                      <td colSpan="9" style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                        <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>🔍</div>
                        <div style={{ fontWeight: 600 }}>No district assessment records found</div>
                        <div style={{ fontSize: '0.85rem' }}>Try clearing the search text or adjusting category / assessment year filters.</div>
                      </td>
                    </tr>
                  ) : (
                    dataRecords.map((r) => (
                      <tr key={r.id}>
                        <td><strong>{r.district_name}</strong></td>
                        <td>{r.state_name}</td>
                        <td>{r.assessment_year}</td>
                        <td>{r.annual_groundwater_recharge_ham !== null && r.annual_groundwater_recharge_ham !== undefined ? Number(r.annual_groundwater_recharge_ham).toLocaleString() : 'N/A'}</td>
                        <td>{r.annual_groundwater_extraction_ham !== null && r.annual_groundwater_extraction_ham !== undefined ? Number(r.annual_groundwater_extraction_ham).toLocaleString() : 'N/A'}</td>
                        <td>
                          <strong>{r.stage_of_groundwater_extraction_percent !== null ? `${r.stage_of_groundwater_extraction_percent}%` : 'N/A'}</strong>
                        </td>
                        <td>
                          <span className={`badge ${getBadgeClass(r.district_assessment_category)}`}>
                            {r.district_assessment_category || 'N/A'}
                          </span>
                        </td>
                        <td>{r.rainfall_mm !== null && r.rainfall_mm !== undefined ? `${r.rainfall_mm} mm` : 'N/A'}</td>
                        <td style={{ textAlign: 'center' }}>
                          <button 
                            className="btn btn-sm btn-primary"
                            onClick={() => handleOpenEdit(r)}
                            style={{ padding: '6px 14px' }}
                          >
                            ✏️ Edit Record
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>

              {/* Pagination */}
              <div className="pagination-container">
                <span>Showing {dataRecords.length} of {dataTotal} district assessment records</span>
                <div className="pagination-controls">
                  <button 
                    className="btn btn-sm btn-outline" 
                    disabled={dataPage <= 1}
                    onClick={() => fetchDataEditorRecords(dataPage - 1)}
                  >
                    ◀ Previous
                  </button>
                  <span style={{ fontWeight: 600, padding: '0 8px' }}>Page {dataPage} of {Math.max(1, Math.ceil(dataTotal / dataPageSize))}</span>
                  <button 
                    className="btn btn-sm btn-outline"
                    disabled={dataPage >= Math.ceil(dataTotal / dataPageSize)}
                    onClick={() => fetchDataEditorRecords(dataPage + 1)}
                  >
                    Next ▶
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* =====================================================================
          MODAL 1: RESET PASSWORD
          ===================================================================== */}
      {resetModalUser && (
        <div className="admin-modal-overlay">
          <div className="admin-modal-container">
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">🔑 Reset User Password</h3>
              <button className="admin-modal-close" onClick={() => setResetModalUser(null)}>×</button>
            </div>
            <form onSubmit={handleResetPassword}>
              <div className="admin-modal-body">
                <p style={{ marginBottom: '15px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                  Set a new password for <strong>{resetModalUser.name}</strong> (<code>{resetModalUser.email}</code>).
                </p>
                <div className="form-group">
                  <label className="form-label" htmlFor="new-pwd-input">New Password</label>
                  <input 
                    id="new-pwd-input"
                    type="password" 
                    className="form-control" 
                    placeholder="Enter new password (min 4 characters)..." 
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={4}
                    autoFocus
                  />
                </div>
              </div>
              <div className="admin-modal-footer">
                <button type="button" className="btn btn-outline" onClick={() => setResetModalUser(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={actionLoading}>
                  {actionLoading ? 'Saving...' : 'Update Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* =====================================================================
          MODAL 2: DELETE USER CONFIRMATION
          ===================================================================== */}
      {deleteModalUser && (
        <div className="admin-modal-overlay">
          <div className="admin-modal-container">
            <div className="admin-modal-header">
              <h3 className="admin-modal-title" style={{ color: '#dc2626' }}>🗑️ Confirm Account Deletion</h3>
              <button className="admin-modal-close" onClick={() => setDeleteModalUser(null)}>×</button>
            </div>
            <div className="admin-modal-body">
              <p style={{ fontSize: '0.95rem', color: 'var(--text-main)', marginBottom: '10px' }}>
                Are you sure you want to permanently delete the following user?
              </p>
              <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', padding: '12px 16px', borderRadius: '6px', marginBottom: '15px' }}>
                <div><strong>Name:</strong> {deleteModalUser.name}</div>
                <div><strong>Email:</strong> {deleteModalUser.email}</div>
                <div><strong>Role:</strong> {deleteModalUser.role}</div>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#991b1b' }}>
                ⚠️ Warning: This will delete the user's account and associated query history permanently.
              </p>
            </div>
            <div className="admin-modal-footer">
              <button type="button" className="btn btn-outline" onClick={() => setDeleteModalUser(null)}>
                Cancel
              </button>
              <button type="button" className="btn btn-danger" onClick={handleDeleteUser} disabled={actionLoading}>
                {actionLoading ? 'Deleting...' : 'Delete User Permanently'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          MODAL 3: EDIT GROUNDWATER DATA RECORD
          ===================================================================== */}
      {editingRecord && (
        <div className="admin-modal-overlay">
          <div className="admin-modal-container modal-lg">
            <div className="admin-modal-header">
              <h3 className="admin-modal-title">
                ✏️ Edit Groundwater Assessment: {editingRecord.district_name}, {editingRecord.state_name} ({editingRecord.assessment_year})
              </h3>
              <button className="admin-modal-close" onClick={() => setEditingRecord(null)}>×</button>
            </div>
            <form onSubmit={handleSaveRecord}>
              <div className="admin-modal-body">
                {/* Row 1: Recharge & Extractable Resource */}
                <div className="form-row-2">
                  <div className="form-group">
                    <label className="form-label">Annual Groundwater Recharge (ha-m)</label>
                    <input 
                      type="number" 
                      step="any"
                      className="form-control" 
                      value={editFormData.annual_groundwater_recharge_ham}
                      onChange={(e) => handleEditInputChange('annual_groundwater_recharge_ham', e.target.value)}
                      placeholder="e.g. 54200.5"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Annual Extractable Resource (ha-m)</label>
                    <input 
                      type="number" 
                      step="any"
                      className="form-control" 
                      value={editFormData.annual_extractable_groundwater_resource_ham}
                      onChange={(e) => handleEditInputChange('annual_extractable_groundwater_resource_ham', e.target.value)}
                      placeholder="e.g. 48780.0"
                    />
                  </div>
                </div>

                {/* Row 2: Extraction & Stage % */}
                <div className="form-row-2">
                  <div className="form-group">
                    <label className="form-label">Annual Groundwater Extraction (ha-m)</label>
                    <input 
                      type="number" 
                      step="any"
                      className="form-control" 
                      value={editFormData.annual_groundwater_extraction_ham}
                      onChange={(e) => handleEditInputChange('annual_groundwater_extraction_ham', e.target.value)}
                      placeholder="e.g. 39800.0"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">
                      Stage of Extraction (%) <span style={{ fontSize: '0.75rem', color: 'var(--primary-color)' }}>(Auto-calculated)</span>
                    </label>
                    <input 
                      type="number" 
                      step="any"
                      className="form-control" 
                      value={editFormData.stage_of_groundwater_extraction_percent}
                      onChange={(e) => handleEditInputChange('stage_of_groundwater_extraction_percent', e.target.value)}
                      placeholder="e.g. 81.5"
                    />
                  </div>
                </div>

                {/* Row 3: Assessment Category & Rainfall */}
                <div className="form-row-2">
                  <div className="form-group">
                    <label className="form-label">Assessment Category</label>
                    <select 
                      className="form-control"
                      value={editFormData.district_assessment_category}
                      onChange={(e) => handleEditInputChange('district_assessment_category', e.target.value)}
                    >
                      <option value="Safe">Safe (&le; 70%)</option>
                      <option value="Semi-Critical">Semi-Critical (70% - 90%)</option>
                      <option value="Critical">Critical (90% - 100%)</option>
                      <option value="Over-Exploited">Over-Exploited (&gt; 100%)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Annual Rainfall (mm)</label>
                    <input 
                      type="number" 
                      step="any"
                      className="form-control" 
                      value={editFormData.rainfall_mm}
                      onChange={(e) => handleEditInputChange('rainfall_mm', e.target.value)}
                      placeholder="e.g. 650.4"
                    />
                  </div>
                </div>

                {/* Row 4: Water Level Depth */}
                <div className="form-group">
                  <label className="form-label">Average Depth to Water Level (meters below ground level)</label>
                  <input 
                    type="number" 
                    step="any"
                    className="form-control" 
                    value={editFormData.depth_to_water_level_m_bgl}
                    onChange={(e) => handleEditInputChange('depth_to_water_level_m_bgl', e.target.value)}
                    placeholder="e.g. 14.8"
                  />
                </div>
              </div>
              <div className="admin-modal-footer">
                <button type="button" className="btn btn-outline" onClick={() => setEditingRecord(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={actionLoading}>
                  {actionLoading ? 'Saving Changes...' : 'Save Groundwater Record 💾'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
