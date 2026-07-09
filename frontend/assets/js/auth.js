// Guarda/lee tokens en localStorage
function guardarTokens(access, refresh) {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
}

function getAccessToken() {
    return localStorage.getItem('access_token');
}

function estaLogueado() {
    return !!getAccessToken();
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = 'login.html';
}

// Login
async function login(username, password) {
    const resp = await fetch(`${API_BASE}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    });
    if (!resp.ok) throw new Error('Usuario o contraseña incorrectos');
    const data = await resp.json();
    guardarTokens(data.access, data.refresh);
}

// Registro
async function registrar(username, email, password) {
    const resp = await fetch(`${API_BASE}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
    });
    if (!resp.ok) {
        const err = await resp.json();
        throw new Error(JSON.stringify(err));
    }
}

// Fetch autenticado (agrega el token automáticamente)
async function fetchAuth(url, options = {}) {
    const token = getAccessToken();
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };
    const resp = await fetch(url, options);
    if (resp.status === 401) {
        logout();
        throw new Error('Sesión expirada');
    }
    return resp;
}
