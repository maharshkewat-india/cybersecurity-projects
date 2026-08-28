/**
 * auth.ts - Authentication helpers.
 */

import { api, getErrorMessage } from "./api";

export interface User {
  id: number;
  username: string;
  role_names: string[];
  permissions: string[];
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  must_change_password: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

/**
 * Attempt to login and store the token.
 */
export async function login(
  username: string,
  password: string
): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>("/auth/login", {
    username,
    password,
  });

  const { access_token, user } = response.data;

  // Store in localStorage
  if (typeof window !== "undefined") {
    localStorage.setItem("forensic_token", access_token);
    localStorage.setItem("forensic_user", JSON.stringify(user));
  }

  return response.data;
}

/**
 * Logout and clear stored credentials.
 */
export function logout(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("forensic_token");
    localStorage.removeItem("forensic_user");
  }
}

/**
 * Get the current user from storage.
 */
export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const userStr = localStorage.getItem("forensic_user");
  if (!userStr) return null;
  try {
    return JSON.parse(userStr) as User;
  } catch {
    return null;
  }
}

/**
 * Get the stored token.
 */
export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("forensic_token");
}

/**
 * Check if the user is authenticated.
 */
export function isAuthenticated(): boolean {
  return !!getStoredToken() && !!getStoredUser();
}

/**
 * Check if the user has a specific permission.
 */
export function hasPermission(permission: string): boolean {
  const user = getStoredUser();
  if (!user) return false;
  return user.permissions.includes(permission);
}

/**
 * Check if the user has any of the specified permissions.
 */
export function hasAnyPermission(permissions: string[]): boolean {
  const user = getStoredUser();
  if (!user) return false;
  return permissions.some((p) => user.permissions.includes(p));
}

/**
 * Check if the user has a specific role.
 */
export function hasRole(role: string): boolean {
  const user = getStoredUser();
  if (!user) return false;
  return user.role_names.includes(role);
}
