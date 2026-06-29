package com.agentrecruit.security;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Component;

import java.time.Duration;

/**
 * refresh_token Cookie 行为复刻 Python 端（backend/api/routes/auth.py）：
 * HttpOnly、path=/api、SameSite=Lax、max-age=refresh 过期天数。
 */
@Component
public class CookieUtil {

    public static final String REFRESH_COOKIE = "refresh_token";
    private static final String PATH = "/api";

    private final boolean secure;
    private final long refreshExpireDays;

    public CookieUtil(
            @Value("${app.cookie.secure}") boolean secure,
            @Value("${app.jwt.refresh-token-expire-days}") long refreshExpireDays) {
        this.secure = secure;
        this.refreshExpireDays = refreshExpireDays;
    }

    public String buildRefreshCookie(String refreshToken) {
        return ResponseCookie.from(REFRESH_COOKIE, refreshToken)
                .httpOnly(true)
                .secure(secure)
                .sameSite("Lax")
                .path(PATH)
                .maxAge(Duration.ofDays(refreshExpireDays))
                .build()
                .toString();
    }

    public String buildClearRefreshCookie() {
        return ResponseCookie.from(REFRESH_COOKIE, "")
                .httpOnly(true)
                .secure(secure)
                .sameSite("Lax")
                .path(PATH)
                .maxAge(0)
                .build()
                .toString();
    }
}
