const API_BASE_URL = 'http://127.0.0.1:5000/api/v1';

// Event listener for DOMContentLoaded to handle login form submission
document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');

  if (loginForm) {
    const errorMessage = createLoginErrorMessage(loginForm);

    loginForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      errorMessage.textContent = '';

      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value.trim();
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

/*
 * Function: createLoginErrorMessage
 * Purpose: Creates or retrieves the error message element for the login form
 * Parameters:
 *   loginForm: The login form element
 * Returns:
 *   The error message element
 */

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

/*
 * Function: loginUser
 * Purpose: Logs in the user by sending a POST request to the login endpoint
 * Parameters:
 *   email: The user's email
 *   password: The user's password
 * Returns:
 *   The parsed JSON response from the server
 */

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
  // store token in localStorage and cookie
  localStorage.setItem('token', data.access_token);
  document.cookie = `token=${encodeURIComponent(data.access_token)}; path=/; SameSite=Lax`;
  window.location.href = 'index.html';
}

/*
 * Function: handleLogin
 * Purpose: Handles the login form submission, validates the input, and logs in the user
 * Parameters:
 *   event: The form submission event
 * Returns:
 *   The parsed JSON response from the server
 */

async function parseJsonResponse(response) {
  try {
    return await response.json();
  } catch (error) {
    return {};
  }
}
