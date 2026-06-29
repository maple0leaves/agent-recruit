package com.agentrecruit.auth;

import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.agentrecruit.auth.dto.UserResponse;
import com.agentrecruit.auth.entity.User;
import com.agentrecruit.auth.mapper.UserMapper;
import com.agentrecruit.common.ApiException;
import com.agentrecruit.security.JwtService;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final LoginRateLimiter rateLimiter;

    public AuthService(UserMapper userMapper,
                       PasswordEncoder passwordEncoder,
                       JwtService jwtService,
                       LoginRateLimiter rateLimiter) {
        this.userMapper = userMapper;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.rateLimiter = rateLimiter;
    }

    /** 登录结果：携带 access/refresh token 与用户信息。 */
    public record LoginResult(String accessToken, String refreshToken, UserResponse user) {
    }

    public LoginResult login(String username, String password) {
        if (rateLimiter.isBlocked(username)) {
            throw new ApiException(429, "登录失败次数过多，请稍后再试");
        }

        User user = findByUsername(username);
        if (user == null || !passwordEncoder.matches(password, user.getHashedPassword())) {
            rateLimiter.recordFailure(username);
            throw ApiException.unauthorized("用户名或密码错误");
        }

        rateLimiter.reset(username);
        String userId = String.valueOf(user.getId());
        String accessToken = jwtService.createAccessToken(userId, user.getRole());
        String refreshToken = jwtService.createRefreshToken(userId, user.getRole());
        UserResponse userResponse = new UserResponse(user.getId(), user.getUsername(), user.getRole());
        return new LoginResult(accessToken, refreshToken, userResponse);
    }

    public void changePassword(String userId, String oldPassword, String newPassword) {
        User user = userMapper.selectById(Long.valueOf(userId));
        if (user == null) {
            throw ApiException.notFound("用户不存在");
        }
        if (!passwordEncoder.matches(oldPassword, user.getHashedPassword())) {
            throw ApiException.badRequest("原密码错误");
        }
        user.setHashedPassword(passwordEncoder.encode(newPassword));
        userMapper.updateById(user);
    }

    private User findByUsername(String username) {
        return userMapper.selectOne(
                Wrappers.<User>lambdaQuery().eq(User::getUsername, username));
    }
}
