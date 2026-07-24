/**
 * Centralized API configuration.
 *
 * All components should import API_BASE_URL from here instead of
 * defining their own `http://localhost:8000` constants.
 */
export const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8088';
