package com.xiaosi.nas.service;

import com.xiaosi.nas.entity.User;
import com.xiaosi.nas.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public List<User> findAll() {
        return userRepository.findAll();
    }

    public Optional<User> findById(Long id) {
        return userRepository.findById(id);
    }

    public Optional<User> findByUsername(String username) {
        return userRepository.findByUsername(username);
    }

    @Transactional
    public User create(User user) {
        if (userRepository.existsByUsername(user.getUsername())) {
            throw new IllegalArgumentException("用户名已存在");
        }
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        return userRepository.save(user);
    }

    @Transactional
    public User update(Long id, User userDetails) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("用户不存在"));
        
        user.setLanguage(userDetails.getLanguage());
        user.setStorageQuota(userDetails.getStorageQuota());
        user.setRole(userDetails.getRole());
        user.setEnabled(userDetails.getEnabled());
        
        return userRepository.save(user);
    }

    @Transactional
    public void delete(Long id) {
        userRepository.deleteById(id);
    }

    @Transactional
    public void updateLastLogin(Long id) {
        userRepository.findById(id).ifPresent(user -> {
            user.setLastLogin(LocalDateTime.now());
            userRepository.save(user);
        });
    }

    @Transactional
    public void updateUsedStorage(Long id, Long additionalBytes) {
        userRepository.findById(id).ifPresent(user -> {
            Long newUsed = user.getUsedStorage() + additionalBytes;
            user.setUsedStorage(Math.max(0, newUsed));
            userRepository.save(user);
        });
    }

    public boolean authenticate(String username, String rawPassword) {
        return userRepository.findByUsername(username)
            .map(user -> passwordEncoder.matches(rawPassword, user.getPassword()))
            .orElse(false);
    }
}