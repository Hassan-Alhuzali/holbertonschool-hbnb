const API_BASE_URL = 'http://127.0.0.1:5000/api/v1';

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');

  if (loginForm) {
    const errorMessage = createLoginErrorMessage(loginForm);

    loginForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      errorMessage.textContent = '';

      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
      const submitButton = loginForm.querySelector('button[type="submit"]');

      if (submitButton) {
        submitButton.disabled = true;
      }

      try {
        await loginUser(email, password);
      } catch (error) {
        errorMessage.textContent = error.message;
      } finally {
        if (submitButton) {
          submitButton.disabled = false;
        }
      }
    });
  }
});

function createLoginErrorMessage(loginForm) {
  let errorMessage = document.getElementById('login-error');

  if (!errorMessage) {
    errorMessage = document.createElement('p');
    errorMessage.id = 'login-error';
    errorMessage.className = 'form-error';
    errorMessage.setAttribute('role', 'alert');
    errorMessage.setAttribute('aria-live', 'polite');
    loginForm.appendChild(errorMessage);
  }

  return errorMessage;
}

async function loginUser(email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  const data = await parseJsonResponse(response);

  if (!response.ok) {
    throw new Error(data.error || data.message || 'Login failed. Please check your credentials.');
  }

  if (!data.access_token) {
    throw new Error('Login failed. The server did not return an access token.');
  }

  document.cookie = `token=${encodeURIComponent(data.access_token)}; path=/; SameSite=Lax`;
  window.location.href = 'index.html';
}

async function parseJsonResponse(response) {
  try {
    return await response.json();
  } catch (error) {
    return {};
  }
}
