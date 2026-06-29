package com.agentrecruit.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;

/**
 * JWT 创建与校验。
 *
 * 与 Python 端 PyJWT 完全兼容：
 * - 算法固定 HS256（{@link Jwts.SIG#HS256}），与 Python decode(algorithms=["HS256"]) 对齐。
 * - HMAC 密钥取 JWT_SECRET 字符串的 UTF-8 原始字节（PyJWT 也是这样处理字符串密钥）。
 * - claims：sub(userId)、role、type(access/refresh)、iat、exp。
 */
@Component
public class JwtService {

    private final String secret;
    private final long accessExpireMinutes;
    private final long refreshExpireDays;
    private SecretKey key;

    public JwtService(
            @Value("${app.jwt.secret}") String secret,
            @Value("${app.jwt.access-token-expire-minutes}") long accessExpireMinutes,
            @Value("${app.jwt.refresh-token-expire-days}") long refreshExpireDays) {
        this.secret = secret;
        this.accessExpireMinutes = accessExpireMinutes;
        this.refreshExpireDays = refreshExpireDays;
    }

    @PostConstruct
    void init() {
        this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }

    public String createAccessToken(String userId, String role) {
        Instant now = Instant.now();
        return Jwts.builder()
                .subject(userId)
                .claim("role", role)
                .claim("type", "access")
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plusSeconds(accessExpireMinutes * 60)))
                .signWith(key, Jwts.SIG.HS256)
                .compact();
    }

    public String createRefreshToken(String userId, String role) {
        Instant now = Instant.now();
        return Jwts.builder()
                .subject(userId)
                .claim("role", role)
                .claim("type", "refresh")
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plusSeconds(refreshExpireDays * 24 * 3600)))
                .signWith(key, Jwts.SIG.HS256)
                .compact();
    }

    /** 解析并校验签名/过期，返回 claims；非法或过期抛异常。 */
    public Claims parse(String token) {
        return Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}
