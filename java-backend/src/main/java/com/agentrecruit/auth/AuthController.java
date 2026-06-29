package com.agentrecruit.auth;

import com.agentrecruit.auth.dto.ChangePasswordRequest;
import com.agentrecruit.auth.dto.LoginRequest;
import com.agentrecruit.auth.dto.LoginResponse;
import com.agentrecruit.common.ApiException;
import com.agentrecruit.security.AuthUser;
import com.agentrecruit.security.CookieUtil;
import com.agentrecruit.security.JwtBlacklist;
import com.agentrecruit.security.JwtService;
import io.jsonwebtoken.Claims;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpHeaders;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;
    private final CookieUtil cookieUtil;
    private final JwtService jwtService;
    private final JwtBlacklist blacklist;

    public AuthController(AuthService authService, CookieUtil cookieUtil,
                          JwtService jwtService, JwtBlacklist blacklist) {
        this.authService = authService;
        this.cookieUtil = cookieUtil;
        this.jwtService = jwtService;
        this.blacklist = blacklist;
    }

    @PostMapping("/login")
    public LoginResponse login(@Valid @RequestBody LoginRequest request, HttpServletResponse response) {
        AuthService.LoginResult result = authService.login(request.username(), request.password());
        response.addHeader(HttpHeaders.SET_COOKIE, cookieUtil.buildRefreshCookie(result.refreshToken()));
        return LoginResponse.of(result.accessToken(), result.user());
    }

    @PostMapping("/logout")
    public Map<String, String> logout(HttpServletRequest request, HttpServletResponse response) {
        String token = resolveToken(request);
        if (token != null) {
            try {
                Claims claims = jwtService.parse(token);
                long ttl = (claims.getExpiration().getTime() - System.currentTimeMillis()) / 1000;
                blacklist.revoke(token, ttl);
            } catch (Exception ignored) {
                // token 已失效，无需拉黑
            }
        }
        response.addHeader(HttpHeaders.SET_COOKIE, cookieUtil.buildClearRefreshCookie());
        return Map.of("message", "已登出");
    }

    @GetMapping("/me")
    public Map<String, String> me() {
        AuthUser user = currentUser();
        Map<String, String> body = new LinkedHashMap<>();
        body.put("sub", user.userId());
        body.put("role", user.role());
        return body;
    }

    @PatchMapping("/password")
    public Map<String, String> changePassword(@Valid @RequestBody ChangePasswordRequest request) {
        AuthUser user = currentUser();
        authService.changePassword(user.userId(), request.old_password(), request.new_password());
        return Map.of("message", "密码修改成功");
    }

    private AuthUser currentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !(auth.getPrincipal() instanceof AuthUser authUser)) {
            throw ApiException.unauthorized("未登录或登录已过期");
        }
        return authUser;
    }

    private String resolveToken(HttpServletRequest request) {
        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            return header.substring(7).trim();
        }
        if (request.getCookies() != null) {
            for (Cookie c : request.getCookies()) {
                if ("access_token".equals(c.getName()) || CookieUtil.REFRESH_COOKIE.equals(c.getName())) {
                    return c.getValue();
                }
            }
        }
        return null;
    }
}
