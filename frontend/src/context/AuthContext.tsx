import {
  createContext,
  useCallback,
  useState,
  type ReactNode,
} from "react";

import { apiService } from "../services/apiService";
import { storageService } from "../services/storageService";
import type { UserPublic } from "../types/user";

export interface AuthContextType {
  isAuthenticated: boolean;
  user: UserPublic | null;
  loading: boolean;
  login: (certificatePem: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(storageService.getUser());
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    !!storageService.getAccessToken()
  );
  const [loading, setLoading] = useState(false);

  const login = useCallback(async (certificatePem: string) => {
    setLoading(true);
    try {
      const res = await apiService.validateCertificate(certificatePem);
      storageService.setAccessToken(res.access_token);
      storageService.setRefreshToken(res.refresh_token);
      storageService.setUser(res.user);
      setUser(res.user);
      setIsAuthenticated(true);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    apiService.logout().catch(() => {
      /* best-effort: invalida en servidor si se puede */
    });
    storageService.clearSession();
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
