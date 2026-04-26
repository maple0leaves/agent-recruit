import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/client";
import { useAuthStore } from "../store/authStore";
import type { AuthUser } from "../store/authStore";

interface LoginParams {
  username: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export function useAuth() {
  const { user, accessToken, setUser, setAccessToken, clearAuth } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Check session on mount / refresh
  const { isLoading } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      try {
        const res = await apiClient.get("/auth/me");
        setUser(res.data);
        return res.data;
      } catch {
        clearAuth();
        throw new Error("Not authenticated");
      }
    },
    retry: false,
    staleTime: 0,
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (params: LoginParams) => {
      const res = await apiClient.post<LoginResponse>("/auth/login", params);
      return res.data;
    },
    onSuccess: (data) => {
      setAccessToken(data.access_token);
      setUser(data.user);
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post("/auth/logout");
    },
    onSuccess: () => {
      clearAuth();
      queryClient.clear();
      navigate("/login");
    },
  });

  return {
    user,
    accessToken,
    isLoading,
    isAuthenticated: !!user,
    login: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    logout: logoutMutation.mutateAsync,
    isLoggingOut: logoutMutation.isPending,
  };
}
