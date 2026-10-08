export interface UserProfile {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  avatar?: string | null;
  language: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  password_confirm?: string;
  first_name?: string;
  last_name?: string;
  language?: string;
}

export interface AuthResponse {
  user: UserProfile;
  access: string;
  refresh: string;
}

export interface UserUpdatePayload {
  first_name?: string;
  last_name?: string;
  language?: string;
}

export interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: UserUpdatePayload) => Promise<UserProfile>;
}
