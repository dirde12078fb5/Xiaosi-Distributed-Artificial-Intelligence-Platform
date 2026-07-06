package storage

import (
	"fmt"
	"os"
	"sync"

	"xiaosi-nas/internal/config"
)

type Manager struct {
	volumes map[string]*Volume
	mu      sync.RWMutex
	cfg     *config.StorageConfig
}

type Volume struct {
	Name     string  `json:"name"`
	Path     string  `json:"path"`
	QuotaGB  int     `json:"quota_gb"`
	UsedGB   float64 `json:"used_gb"`
	ReadOnly bool    `json:"read_only"`
}

func NewManager(cfg *config.StorageConfig) *Manager {
	m := &Manager{
		volumes: make(map[string]*Volume),
		cfg:     cfg,
	}
	for _, v := range cfg.Volumes {
		m.volumes[v.Name] = &Volume{
			Name:     v.Name,
			Path:     v.Path,
			QuotaGB:  v.QuotaGB,
			UsedGB:   0,
			ReadOnly: false,
		}
	}
	return m
}

func (m *Manager) ListVolumes() []*Volume {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*Volume, 0, len(m.volumes))
	for _, v := range m.volumes {
		result = append(result, &Volume{
			Name:     v.Name,
			Path:     v.Path,
			QuotaGB:  v.QuotaGB,
			UsedGB:   v.UsedGB,
			ReadOnly: v.ReadOnly,
		})
	}
	return result
}

func (m *Manager) GetVolume(name string) (*Volume, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	v, ok := m.volumes[name]
	if !ok {
		return nil, fmt.Errorf("volume not found: %s", name)
	}
	return v, nil
}

func (m *Manager) CreateVolume(name, path string, quotaGB int) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, ok := m.volumes[name]; ok {
		return fmt.Errorf("volume already exists: %s", name)
	}

	if err := os.MkdirAll(path, 0755); err != nil {
		return fmt.Errorf("failed to create volume path: %w", err)
	}

	m.volumes[name] = &Volume{
		Name:    name,
		Path:    path,
		QuotaGB: quotaGB,
	}
	return nil
}

func (m *Manager) DeleteVolume(name string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, ok := m.volumes[name]; !ok {
		return fmt.Errorf("volume not found: %s", name)
	}
	delete(m.volumes, name)
	return nil
}

func (m *Manager) UpdateQuota(name string, quotaGB int) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	v, ok := m.volumes[name]
	if !ok {
		return fmt.Errorf("volume not found: %s", name)
	}
	v.QuotaGB = quotaGB
	return nil
}

func (m *Manager) GetStorageStats(name string) (used, available int64, err error) {
	v, err := m.GetVolume(name)
	if err != nil {
		return 0, 0, err
	}

	available = int64(v.QuotaGB) * 1024 * 1024 * 1024
	used = int64(v.UsedGB * 1024 * 1024 * 1024)
	return used, available - used, nil
}

func (m *Manager) UpdateUsage(name string, usedGB float64) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	v, ok := m.volumes[name]
	if !ok {
		return fmt.Errorf("volume not found: %s", name)
	}
	v.UsedGB = usedGB
	return nil
}