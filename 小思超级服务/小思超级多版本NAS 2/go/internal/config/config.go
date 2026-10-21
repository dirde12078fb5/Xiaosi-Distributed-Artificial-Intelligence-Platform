package config

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type Config struct {
	Server  ServerConfig  `json:"server"`
	Storage StorageConfig `json:"storage"`
	SMB     SMBConfig     `json:"smb"`
	I18n    I18nConfig    `json:"i18n"`
	Push    PushConfig    `json:"push"`
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
	Name    string `json:"name"`
	Path    string `json:"path"`
	QuotaGB int    `json:"quota_gb"`
}

type SMBConfig struct {
	Enabled   bool   `json:"enabled"`
	Port      int    `json:"port"`
	Workgroup string `json:"workgroup"`
}

type I18nConfig struct {
	Default   string   `json:"default"`
	Supported []string `json:"supported"`
}

type PushConfig struct {
	Enabled  bool   `json:"enabled"`
	Provider string `json:"provider"`
	Token    string `json:"token"`
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

func GetConfigPath() string {
	// 从go目录向上查找config目录
	execPath, _ := os.Executable()
	baseDir := filepath.Dir(filepath.Dir(execPath))
	return filepath.Join(baseDir, "config", "config.json")
}

func DefaultConfig() *Config {
	return &Config{
		Server: ServerConfig{
			Host:     "0.0.0.0",
			Port:     8082,
			Language: "zh_CN",
		},
		Storage: StorageConfig{
			Volumes: []VolumeConfig{
				{Name: "data", Path: "./data", QuotaGB: 1000},
			},
		},
		SMB: SMBConfig{
			Enabled:   true,
			Port:      445,
			Workgroup: "WORKGROUP",
		},
		I18n: I18nConfig{
			Default: "zh_CN",
			Supported: []string{
				"zh_CN", "zh_TW", "en_US", "en_GB", "ja_JP", "ko_KR",
				"fr_FR", "de_DE", "es_ES", "it_IT", "pt_BR", "ru_RU",
				"ar_SA", "hi_IN", "tr_TR", "th_TH", "vi_VN", "id_ID",
				"nl_NL", "pl_PL", "sv_SE", "da_DK", "fi_FI", "he_IL",
				"hu_HU", "cs_CZ", "uk_UA", "ro_RO",
			},
		},
		Push: PushConfig{
			Enabled:  false,
			Provider: "websocket",
		},
	}
}