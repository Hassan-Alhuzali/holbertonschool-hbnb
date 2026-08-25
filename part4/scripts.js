const API_BASE_URL = 'http://127.0.0.1:5000/api/v1';

// Event listener for DOMContentLoaded to handle login form submission
document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');

  // Check user authentication status on page load
  checkAuthentication();

  // Setup event listener for the price filter dropdown
  const priceFilter = document.getElementById('price-filter');
  if (priceFilter) {
    priceFilter.addEventListener('change', (event) => {
      const selectedPrice = event.target.value;
      const placesList = document.querySelectorAll('.place-card');

      placesList.forEach(place => {
        const price = parseFloat(place.getAttribute('data-price'));
        if (selectedPrice === 'All' || price <= parseFloat(selectedPrice)) {
          place.style.display = 'block';
        } else {
          place.style.display = 'none';
        }
      });
    });
  }

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

/*
 * Function: getCookie
 * Purpose: Retrieves the value of a specific cookie by its name
 * Parameters:
 *   name: The name of the cookie to retrieve
 * Returns:
 *   The value of the cookie if found, otherwise null
 */
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  // Fallback to localStorage (especially for file:/// testing where cookies fail)
  return localStorage.getItem(name);
}

/*
 * Function: checkAuthentication
 * Purpose: Checks if the user is authenticated by verifying the presence of a token
 *          and updates the login link display accordingly
 */
function checkAuthentication() {
  const token = getCookie('token');
  const loginLink = document.getElementById('login-link');

  if (loginLink) {
    if (!token) {
      loginLink.style.display = 'inline-block';
    } else {
      loginLink.style.display = 'none';
    }
  }

  const placesList = document.getElementById('places-list');
  if (placesList) {
    fetchPlaces(token);
  }

  const placeDetailsSection = document.getElementById('place-details');
  if (placeDetailsSection) {
    const placeId = getPlaceIdFromURL();
    if (placeId) {
      const addReviewSection = document.getElementById('add-review');
      if (addReviewSection) {
        if (!token) {
          addReviewSection.style.display = 'none';
        } else {
          addReviewSection.style.display = 'block';
        }
      }
      fetchPlaceDetails(token, placeId);
    }
  }
}


/*
 * Function: fetchPlaces
 * Purpose: Fetches the list of places dynamically from the API, passing JWT token if available
 * Parameters:
 *   token: The JWT authentication token (optional)
 */
async function fetchPlaces(token) {
  try {
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/places/`, {
      method: 'GET',
      headers: headers
    });

    if (response.ok) {
      const places = await response.json();
      displayPlaces(places);
    } else {
      console.error('Failed to fetch places');
    }
  } catch (error) {
    console.error('Error fetching places:', error);
  }
}

/*
 * Function: displayPlaces
 * Purpose: Dynamically renders and appends the fetched places into the HTML DOM list
 * Parameters:
 *   places: Array of place payload objects returned from the backend API
 */
function displayPlaces(places) {
  const placesList = document.getElementById('places-list');
  if (!placesList) return;

  placesList.innerHTML = ''; // Clear current content

  places.forEach(place => {
    const article = document.createElement('article');
    article.className = 'place-card';
    article.setAttribute('data-price', place.price_by_night || place.price);

    const title = document.createElement('h2');
    title.textContent = place.title || place.name;

    const price = document.createElement('p');
    price.className = 'price';
    price.innerHTML = `$${place.price_by_night || place.price} <span>per night</span>`;

    const description = document.createElement('p');
    description.textContent = place.description;

    const detailsBtn = document.createElement('a');
    detailsBtn.className = 'details-button';
    detailsBtn.href = `place.html?id=${place.id}`;
    detailsBtn.textContent = 'View Details';

    article.appendChild(title);
    article.appendChild(price);
    article.appendChild(description);
    article.appendChild(detailsBtn);

    placesList.appendChild(article);
  });
}

/*
 * Function: getPlaceIdFromURL
 * Purpose: Extract the place ID from the query parameters
 */
function getPlaceIdFromURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get('id');
}

/*
 * Function: fetchPlaceDetails
 * Purpose: Use the Fetch API to get the details of the place and handle the response
 */
async function fetchPlaceDetails(token, placeId) {
  try {
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`; // Include the token in the Authorization header
    }

    const response = await fetch(`${API_BASE_URL}/places/${placeId}`, {
      method: 'GET',
      headers: headers
    });

    if (response.ok) {
      const place = await response.json();
      displayPlaceDetails(place);
    } else {
      console.error('Failed to fetch place details');
    }
  } catch (error) {
    console.error('Error fetching place details:', error);
  }
}

/*
 * Function: displayPlaceDetails
 * Purpose: Dynamically create HTML elements to display the place's detailed information
 */
function displayPlaceDetails(place) {
  const placeDetails = document.getElementById('place-details');
  if (!placeDetails) return;

  placeDetails.innerHTML = ''; // Clear the current content

  const placeInfoHtml = `
    <div class="place-info">
      <h1>${place.name || place.title || 'Name'}</h1>
      <p class="price">$${place.price_by_night || place.price} <span>per night</span></p>
      <p><strong>Host:</strong> ${place.host_name || 'Host'}</p>
      <p>${place.description || ''}</p>
    </div>
  `;

  let amenitiesHtml = `
    <section class="amenities" aria-labelledby="amenities-title">
      <h2 id="amenities-title">Amenities</h2>
      <ul>
  `;
  if (place.amenities && place.amenities.length > 0) {
    place.amenities.forEach(am => {
      amenitiesHtml += `<li><img src="images/icon_wifi.png" alt="" onerror="this.style.display='none'">${am.name || am}</li>`;
    });
  } else {
    amenitiesHtml += `<li>None</li>`;
  }
  amenitiesHtml += `</ul></section>`;

  const addReviewBtnHTML = `<a id="add-review" class="details-button" href="add_review.html?place_id=${place.id}">Add a Review</a>`;

  placeDetails.innerHTML = placeInfoHtml + amenitiesHtml + addReviewBtnHTML;

  const token = getCookie('token');
  const addReviewSection = document.getElementById('add-review');
  if (addReviewSection) {
    if (!token) {
      addReviewSection.style.display = 'none';
    } else {
      addReviewSection.style.display = 'block';
    }
  }

  const reviewsSection = document.querySelector('.reviews-section');
  if (reviewsSection) {
    reviewsSection.innerHTML = '<h2 id="reviews-title">Reviews</h2>';
    if (place.reviews && place.reviews.length > 0) {
      place.reviews.forEach(review => {
        const rating = review.rating || 0;
        const starsText = "★".repeat(rating) + "☆".repeat(5 - rating);
        reviewsSection.innerHTML += `
          <article class="review-card">
            <h3>${review.user_name || review.author || 'User'} <span aria-label="${rating} out of 5 stars">${starsText}</span></h3>
            <p>${review.text || review.comment || ''}</p>
          </article>
        `;
      });
    } else {
      reviewsSection.innerHTML += `<p>No reviews yet.</p>`;
    }
  }
}
