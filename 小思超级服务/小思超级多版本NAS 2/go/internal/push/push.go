package push

import (
	"encoding/json"
	"log"
	"sync"
	"time"

	"xiaosi-nas/internal/config"
)

type Manager struct {
	cfg      *config.PushConfig
	clients  map[string]*Client
	mu       sync.RWMutex
	messages []Message
}

type Client struct {
	ID       string    `json:"id"`
	Name     string    `json:"name"`
	LastSeen time.Time `json:"last_seen"`
}

type Message struct {
	ID        string                 `json:"id"`
	Type      string                 `json:"type"`
	Title     string                 `json:"title"`
	Content   string                 `json:"content"`
	Data      map[string]interface{} `json:"data,omitempty"`
	Timestamp time.Time              `json:"timestamp"`
	Read      bool                   `json:"read"`
}

func NewManager(cfg *config.PushConfig) *Manager {
	return &Manager{
		cfg:      cfg,
		clients:  make(map[string]*Client),
		messages: make([]Message, 0),
	}
}

func (m *Manager) RegisterClient(id, name string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.clients[id] = &Client{
		ID:       id,
		Name:     name,
		LastSeen: time.Now(),
	}
	log.Printf("Client registered: %s (%s)", name, id)
}

func (m *Manager) UnregisterClient(id string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	delete(m.clients, id)
	log.Printf("Client unregistered: %s", id)
}

func (m *Manager) ListClients() []*Client {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*Client, 0, len(m.clients))
	for _, c := range m.clients {
		result = append(result, c)
	}
	return result
}

func (m *Manager) PushMessage(msgType, title, content string, data map[string]interface{}) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	msg := Message{
		ID:        generateID(),
		Type:      msgType,
		Title:     title,
		Content:   content,
		Data:      data,
		Timestamp: time.Now(),
		Read:      false,
	}

	m.messages = append(m.messages, msg)
	log.Printf("Message pushed: %s - %s", msgType, title)
	return nil
}

func (m *Manager) ListMessages(unreadOnly bool) []Message {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]Message, 0)
	for _, msg := range m.messages {
		if !unreadOnly || !msg.Read {
			result = append(result, msg)
		}
	}
	return result
}

func (m *Manager) MarkRead(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	for i, msg := range m.messages {
		if msg.ID == id {
			m.messages[i].Read = true
			return nil
		}
	}
	return nil
}

func (m *Manager) ClearMessages() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.messages = make([]Message, 0)
}

func (m *Manager) GetStatus() map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()

	return map[string]interface{}{
		"enabled":      m.cfg.Enabled,
		"provider":     m.cfg.Provider,
		"clients":      len(m.clients),
		"messages":     len(m.messages),
		"unread":       m.countUnread(),
	}
}

func (m *Manager) countUnread() int {
	count := 0
	for _, msg := range m.messages {
		if !msg.Read {
			count++
		}
	}
	return count
}

func (m *Manager) Broadcast(msgType, title, content string) {
	data, _ := json.Marshal(map[string]interface{}{
		"type":    msgType,
		"title":   title,
		"content": content,
		"time":    time.Now().Format(time.RFC3339),
	})

	m.mu.RLock()
	defer m.mu.RUnlock()

	for _, client := range m.clients {
		log.Printf("Broadcasting to client %s: %s", client.ID, string(data))
	}
}

func generateID() string {
	return time.Now().Format("20060102150405") + randomSuffix()
}

func randomSuffix() string {
	const chars = "abcdefghijklmnopqrstuvwxyz0123456789"
	b := make([]byte, 6)
	for i := range b {
		b[i] = chars[i%len(chars)]
	}
	return string(b)
}