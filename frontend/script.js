// Simple localStorage-based auth mock
function getUsers() {
    const data = localStorage.getItem('tuckdata-users');
    return data ? JSON.parse(data) : [];
}

function saveUsers(users) {
    localStorage.setItem('tuckdata-users', JSON.stringify(users));
}

function signup(username, password) {
    const users = getUsers();
    if (users.find(u => u.username === username)) {
        alert('User already exists');
        return false;
    }
    users.push({ username, password });
    saveUsers(users);
    return true;
}

function login(username, password) {
    const users = getUsers();
    const user = users.find(u => u.username === username && u.password === password);
    if (user) {
        localStorage.setItem('tuckdata-current', username);
        return true;
    }
    return false;
}

function logout() {
    localStorage.removeItem('tuckdata-current');
}

function currentUser() {
    return localStorage.getItem('tuckdata-current');
}

// Sign-up form handler
const signupForm = document.getElementById('signup-form');
if (signupForm) {
    signupForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const user = document.getElementById('signup-username').value;
        const pass = document.getElementById('signup-password').value;
        if (signup(user, pass)) {
            alert('Sign up successful. Please log in.');
            window.location.href = 'login.html';
        }
    });
}

// Login form handler
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const user = document.getElementById('login-username').value;
        const pass = document.getElementById('login-password').value;
        if (login(user, pass)) {
            window.location.href = 'dashboard.html';
        } else {
            alert('Invalid credentials');
        }
    });
}

// Dashboard greeting and logout handler
const greeting = document.getElementById('greeting');
if (greeting) {
    const user = currentUser();
    if (!user) {
        window.location.href = 'login.html';
    } else {
        greeting.textContent = `Hello, ${user}!`;
    }
}

const logoutButton = document.getElementById('logout');
if (logoutButton) {
    logoutButton.addEventListener('click', () => {
        logout();
        window.location.href = 'login.html';
    });
}
