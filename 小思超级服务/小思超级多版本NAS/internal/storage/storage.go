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
	Name     string
	Path     string
	QuotaGB  int
	UsedGB   float64
	ReadOnly bool
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

	var stat os.FileInfo
	stat, err = os.Stat(v.Path)
	if err != nil {
		return 0, 0, err
	}

	// 简单返回磁盘使用情况
	available = int64(v.QuotaGB) * 1024 * 1024 * 1024
	used = int64(v.UsedGB * 1024 * 1024 * 1024)
	return used, available - used, nil
}
