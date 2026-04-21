import { useState, useEffect, useCallback } from 'react';
import { authApi, LoginCredentials, AuthResponse } from '../api/auth';

interface AuthState {
  user: AuthResponse['user'] | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: localStorage.getItem('access_token'),
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      authApi
        .getMe()
        .then((user) => {
          setState({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        })
        .catch(() => {
          localStorage.removeItem('access_token');
          setState({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        });
    } else {
      setState((prev) => ({ ...prev, isLoading: false }));
    }
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const response = await authApi.login(credentials);
      localStorage.setItem('access_token', response.access_token);
      setState({
        user: response.user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      return response;
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Login failed';
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: message,
      }));
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    login,
    logout,
  };
}
