const BASE = '/api';

function getToken() {
  return localStorage.getItem('eka_token');
}

function getUser() {
  const raw = localStorage.getItem('eka_user');
  try {
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

async function request(method, path, body) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    localStorage.removeItem('eka_token');
    localStorage.removeItem('eka_user');
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  if (res.status === 204) return null;
  return res.json();
}

export async function login(username, password) {
  const res = await fetch(`${BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Login failed' }));
    let msg = 'Login failed';
    if (typeof err.detail === 'string') {
      msg = err.detail;
    } else if (Array.isArray(err.detail) && err.detail.length > 0) {
      msg = err.detail[0]?.msg || JSON.stringify(err.detail);
    } else if (typeof err.detail === 'object') {
      msg = JSON.stringify(err.detail);
    }
    throw new Error(msg);
  }

  const data = await res.json();
  localStorage.setItem('eka_token', data.access_token);
  localStorage.setItem('eka_user', JSON.stringify({
    username: data.username,
    tenant: data.tenant,
    role: data.role,
  }));
  return data;
}

export function logout() {
  localStorage.removeItem('eka_token');
  localStorage.removeItem('eka_user');
  window.location.href = '/login';
}

export function getCurrentUser() {
  return getUser();
}

export function isAuthenticated() {
  return !!getToken();
}

export const get = (path) => request('GET', path);
export const post = (path, body) => request('POST', path, body);

// Incidents
export const getIncidents = () => get('/incidents');
export const getIncident = (id) => get(`/incidents/${id}`);

// Approvals
export const getApprovals = () => get('/approvals');
export const approve = (id) => post(`/approvals/${id}/approve`, {});
export const reject = (id) => post(`/approvals/${id}/reject`, {});

// Simulate
export const getScenarios = () => get('/scenarios');
export const simulate = (scenarioId) => post('/simulate', { scenario_id: scenarioId });

// Audit
export const getAudit = () => get('/audit');
export const verifyAudit = () => get('/audit/verify');

// Metrics
export const getMetrics = () => get('/metrics');

// Knowledge Base
export const getKnowledge = () => get('/knowledge');

