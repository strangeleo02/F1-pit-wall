/**
 * PitWall AI Frontend Centralized API & Service Configuration.
 * Dynamically resolves backend endpoints using NEXT_PUBLIC_API_BASE_URL environment variable,
 * with automatic fallback to http://localhost:8000.
 */

export const API_BASE_URL: string =
  (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_BASE_URL)
    ? process.env.NEXT_PUBLIC_API_BASE_URL
    : 'http://localhost:8000';

export const API_ENDPOINTS = {
  HEALTH: `${API_BASE_URL}/health`,
  STRATEGY_QUERY: `${API_BASE_URL}/api/v1/strategy/query`,
  STRATEGY_STREAM: `${API_BASE_URL}/api/v1/strategy/stream`,
  SEASONS: `${API_BASE_URL}/api/v1/meta/seasons`,
  SCHEDULE: `${API_BASE_URL}/api/v1/meta/schedule`,
  DRIVERS: `${API_BASE_URL}/api/v1/meta/drivers`,
  WEATHER: `${API_BASE_URL}/api/v1/meta/weather`,
  CIRCUIT: `${API_BASE_URL}/api/v1/meta/circuit`,
  SIMULATE_UNDERCUT: `${API_BASE_URL}/api/v1/simulate/undercut`,
  SIMULATE_SAFETY_CAR: `${API_BASE_URL}/api/v1/simulate/safety-car`,
  HISTORY_DRIVERS: `${API_BASE_URL}/api/v1/history/drivers`,
  HISTORY_CONSTRUCTORS: `${API_BASE_URL}/api/v1/history/constructors`,
};
