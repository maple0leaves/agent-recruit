import axios from "axios";
import { toast } from "sonner";
import { useAuthStore } from "../store/authStore";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: attach access token from auth store
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: unified error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const message =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      "请求失败，请稍后重试";

    if (status === 401 && window.location.pathname !== "/login") {
      window.location.href = "/login";
    } else if (status === 403) {
      toast.error("权限不足", { description: message });
    } else if (status && status >= 500) {
      toast.error("服务器错误", { description: message });
    } else if (status && status >= 400) {
      toast.error("操作失败", { description: message });
    }

    return Promise.reject(error);
  },
);

export default apiClient;
