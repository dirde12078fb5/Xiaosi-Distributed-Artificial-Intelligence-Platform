package user

import (
	"fmt"
	"sync"

	"golang.org/x/crypto/bcrypt"
)

type Manager struct {
	users map[string]*User
	mu    sync.RWMutex
}

type User struct {
	Username     string   `json:"username"`
	Password     string   `json:"-"`
	Groups       []string `json:"groups"`
	HomeDir      string   `json:"home_dir"`
	StorageQuota int      `json:"storage_quota_gb"`
	IsAdmin      bool     `json:"is_admin"`
}

func NewManager() *Manager {
	m := &Manager{
		users: make(map[string]*User),
	}
	// 创建默认管理员
	hash, _ := bcrypt.GenerateFromPassword([]byte("admin"), bcrypt.DefaultCost)
	m.users["admin"] = &User{
		Username:     "admin",
		Password:     string(hash),
		HomeDir:      "/data/admin",
		StorageQuota: 0,
		IsAdmin:      true,
		Groups:       []string{"administrators"},
	}
	return m
}

func (m *Manager) ListUsers() []*User {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*User, 0, len(m.users))
	for _, u := range m.users {
		result = append(result, &User{
			Username:     u.Username,
			Groups:       u.Groups,
			HomeDir:      u.HomeDir,
			StorageQuota: u.StorageQuota,
			IsAdmin:      u.IsAdmin,
		})
	}
	return result
}

func (m *Manager) GetUser(username string) (*User, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	u, ok := m.users[username]
	if !ok {
		return nil, fmt.Errorf("user not found: %s", username)
	}
	return u, nil
}

func (m *Manager) CreateUser(username, password string, isAdmin bool) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, ok := m.users[username]; ok {
		return fmt.Errorf("user already exists: %s", username)
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("password hash failed: %w", err)
	}

	m.users[username] = &User{
		Username:     username,
		Password:     string(hash),
		Groups:       []string{"users"},
		HomeDir:      fmt.Sprintf("/data/%s", username),
		StorageQuota: 100,
		IsAdmin:      isAdmin,
	}
	return nil
}

func (m *Manager) DeleteUser(username string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if username == "admin" {
		return fmt.Errorf("cannot delete admin user")
	}

	if _, ok := m.users[username]; !ok {
		return fmt.Errorf("user not found: %s", username)
	}
	delete(m.users, username)
	return nil
}

func (m *Manager) UpdatePassword(username, newPassword string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	u, ok := m.users[username]
	if !ok {
		return fmt.Errorf("user not found: %s", username)
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("password hash failed: %w", err)
	}

	u.Password = string(hash)
	return nil
}

func (m *Manager) VerifyPassword(username, password string) bool {
	m.mu.RLock()
	defer m.mu.RUnlock()

	u, ok := m.users[username]
	if !ok {
		return false
	}

	err := bcrypt.CompareHashAndPassword([]byte(u.Password), []byte(password))
	return err == nil
}

func (m *Manager) SetStorageQuota(username string, quotaGB int) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	u, ok := m.users[username]
	if !ok {
		return fmt.Errorf("user not found: %s", username)
	}
	u.StorageQuota = quotaGB
	return nil
}

func (m *Manager) SetHomeDir(username string, homeDir string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	u, ok := m.users[username]
	if !ok {
		return fmt.Errorf("user not found: %s", username)
	}
	u.HomeDir = homeDir
	return nil
}