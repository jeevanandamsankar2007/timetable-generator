const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const fetchApi = async (endpoint, options = {}) => {
  const token = localStorage.getItem('token');
  
  const headers = {
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Set default Content-Type to JSON if not sending FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle unauthorized responses (e.g., token expired)
  if (response.status === 401) {
    localStorage.removeItem('token');
    window.dispatchEvent(new Event('auth-error'));
  }

  // Parse JSON response if applicable
  let data;
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.indexOf("application/json") !== -1) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    let errorMessage = 'An error occurred';
    if (data.detail) {
      errorMessage = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    } else if (data.message) {
      errorMessage = typeof data.message === 'string' ? data.message : JSON.stringify(data.message);
    } else if (typeof data === 'string') {
      errorMessage = data;
    } else {
      errorMessage = JSON.stringify(data);
    }
    throw new Error(errorMessage);
  }

  return data;
};

export const downloadFile = async (endpoint, filename) => {
  const token = localStorage.getItem('token');
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem('token');
    window.dispatchEvent(new Event('auth-error'));
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    let errorMessage = 'Failed to download file';
    try {
      const data = await response.json();
      if (data.detail) errorMessage = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    } catch (e) {
      // Not JSON
    }
    throw new Error(errorMessage);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  
  // Try to extract filename from Content-Disposition header if not provided
  let finalFilename = filename;
  if (!finalFilename) {
    const disposition = response.headers.get('content-disposition');
    if (disposition && disposition.includes('filename=')) {
      const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
      if (filenameMatch && filenameMatch.length > 1) {
        finalFilename = filenameMatch[1];
      }
    }
    if (!finalFilename) finalFilename = 'download';
  }
  
  a.download = finalFilename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
};

export const api = {
  get: (endpoint, options = {}) => fetchApi(endpoint, { ...options, method: 'GET' }),
  post: (endpoint, body, options = {}) => {
    return fetchApi(endpoint, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  },
  put: (endpoint, body, options = {}) => fetchApi(endpoint, {
    ...options,
    method: 'PUT',
    body: body instanceof FormData ? body : JSON.stringify(body),
  }),
  delete: (endpoint, options = {}) => fetchApi(endpoint, { ...options, method: 'DELETE' }),
  download: (endpoint, filename) => downloadFile(endpoint, filename),
};
