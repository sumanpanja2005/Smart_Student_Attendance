const TOKEN_KEY = 'smart_attendance_access_token';

export const getToken = () => {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch (err) {
    return null;
  }
};

export const setToken = (token) => {
  try {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    }
  } catch (err) {
    console.error('Failed to save access token:', err);
  }
};

export const removeToken = () => {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch (err) {
    console.error('Failed to remove access token:', err);
  }
};
