package com.xiaosi.nas.controller;

import com.xiaosi.nas.entity.User;
import com.xiaosi.nas.service.UserService;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.time.LocalDateTime;
import java.util.Date;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final UserService userService;

    @Value("${jwt.secret:xiaosi-nas-secret-key-2024-minimum-256-bits-required}")
    private String jwtSecret;

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> credentials) {
        String username = credentials.get("username");
        String password = credentials.get("password");

        if (userService.authenticate(username, password)) {
            User user = userService.findByUsername(username).orElse(null);
            if (user != null && user.getEnabled()) {
                userService.updateLastLogin(user.getId());
                
                String token = Jwts.builder()
                    .subject(username)
                    .claim("userId", user.getId())
                    .claim("role", user.getRole())
                    .issuedAt(new Date())
                    .expiration(new Date(System.currentTimeMillis() + 86400000)) // 24小时
                    .signWith(Keys.hmacShaKeyFor(jwtSecret.getBytes()))
                    .compact();

                return ResponseEntity.ok(Map.of(
                    "token", token,
                    "user", Map.of(
                        "id", user.getId(),
                        "username", user.getUsername(),
                        "role", user.getRole(),
                        "language", user.getLanguage()
                    )
                ));
            }
        }
        
        return ResponseEntity.badRequest().body(Map.of("error", "用户名或密码错误"));
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody User user) {
        try {
            user.setRole("user");
            user.setLanguage("zh-CN");
            user.setEnabled(true);
            User created = userService.create(user);
            
            return ResponseEntity.ok(Map.of(
                "id", created.getId(),
                "username", created.getUsername(),
                "message", "注册成功"
            ));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/validate")
    public ResponseEntity<Map<String, Object>> validateToken(@RequestParam String token) {
        try {
            var claims = Jwts.parser()
                .verifyWith(Keys.hmacShaKeyFor(jwtSecret.getBytes()))
                .build()
                .parseSignedClaims(token);
            
            return ResponseEntity.ok(Map.of(
                "valid", true,
                "username", claims.getPayload().getSubject(),
                "userId", claims.getPayload().get("userId")
            ));
        } catch (Exception e) {
            return ResponseEntity.ok(Map.of("valid", false));
        }
    }
}