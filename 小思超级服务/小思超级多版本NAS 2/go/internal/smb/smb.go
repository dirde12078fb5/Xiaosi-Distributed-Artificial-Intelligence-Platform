package smb

import (
	"fmt"
	"log"
	"sync"

	"xiaosi-nas/internal/config"
)

type Server struct {
	cfg     *config.SMBConfig
	shares  map[string]*Share
	mu      sync.RWMutex
	running bool
}

type Share struct {
	Name        string `json:"name"`
	Path        string `json:"path"`
	Comment     string `json:"comment"`
	ReadOnly    bool   `json:"read_only"`
	Browseable  bool   `json:"browseable"`
	GuestAccess bool   `json:"guest_access"`
}

func NewServer(cfg *config.SMBConfig) *Server {
	return &Server{
		cfg:    cfg,
		shares: make(map[string]*Share),
	}
}

func (s *Server) Start() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.running {
		return fmt.Errorf("SMB server already running")
	}

	s.running = true
	log.Printf("SMB server starting on port %d (workgroup: %s)", s.cfg.Port, s.cfg.Workgroup)
	return nil
}

func (s *Server) Stop() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.running = false
	log.Println("SMB server stopped")
	return nil
}

func (s *Server) IsRunning() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.running
}

func (s *Server) ListShares() []*Share {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]*Share, 0, len(s.shares))
	for _, share := range s.shares {
		result = append(result, share)
	}
	return result
}

func (s *Server) GetShare(name string) (*Share, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	share, ok := s.shares[name]
	if !ok {
		return nil, fmt.Errorf("share not found: %s", name)
	}
	return share, nil
}

func (s *Server) CreateShare(name, path string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, ok := s.shares[name]; ok {
		return fmt.Errorf("share already exists: %s", name)
	}

	s.shares[name] = &Share{
		Name:        name,
		Path:        path,
		Browseable:  true,
		ReadOnly:    false,
		GuestAccess: false,
	}
	return nil
}

func (s *Server) DeleteShare(name string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, ok := s.shares[name]; !ok {
		return fmt.Errorf("share not found: %s", name)
	}
	delete(s.shares, name)
	return nil
}

func (s *Server) UpdateShare(name string, share *Share) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	_, ok := s.shares[name]
	if !ok {
		return fmt.Errorf("share not found: %s", name)
	}

	s.shares[name] = share
	return nil
}

func (s *Server) GetStatus() map[string]interface{} {
	s.mu.RLock()
	defer s.mu.RUnlock()

	return map[string]interface{}{
		"enabled":   s.cfg.Enabled,
		"port":      s.cfg.Port,
		"workgroup": s.cfg.Workgroup,
		"running":   s.running,
		"shares":    len(s.shares),
	}
}