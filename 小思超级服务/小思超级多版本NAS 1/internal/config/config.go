package config

import (
	"encoding/json"
	"os"
)

type Config struct {
	Server  ServerConfig   `json:"server"`
	Storage StorageConfig  `json:"storage"`
	SMB     SMBConfig      `json:"smb"`
	I18n    I18nConfig      `json:"i18n"`
}

type ServerConfig struct {
	Host     string `json:"host"`
	Port     int    `json:"port"`
	Language string `json:"language"`
}

type StorageConfig struct {
	Volumes []VolumeConfig `json:"volumes"`
}

type VolumeConfig struct {
	Name     string `json:"name"`
	Path     string `json:"path"`
	QuotaGB  int    `json:"quota_gb"`
}

type SMBConfig struct {
	Enabled   bool   `json:"enabled"`
	Port      int    `json:"port"`
	Workgroup string `json:"workgroup"`
}

type I18nConfig struct {
	Default    string   `json:"default"`
	Supported  []string `json:"supported"`
}

func Load(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var cfg Config
	if err := json.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}

	return &cfg, nil
}

func (c *Config) Save(path string) error {
	data, err := json.MarshalIndent(c, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0644)
}
