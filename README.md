# 💕 Dr. Harmony - AI Family Psychologist & Secret Keeper

> **Personal AI consultant for couples** - Your mediator, love keeper, and relationship advisor

## 🌟 Features

### **🤖 AI-Powered Relationship Counseling**
- **Gemini 2.5 Pro** as primary AI engine
- **OpenAI GPT** as fallback option
- Natural conversation with psychological insights
- Automatic profile updates based on conversations

### **👥 Multi-User Support**
- **Individual profiles** for each partner
- **Shared context** across all interactions
- **Hidden profiles** for AI's private observations
- **Unlimited users** support

### **📱 Dual Interface**
- **Telegram Bot** - Mobile-friendly chat
- **Web Interface** - Beautiful romantic UI with themes
- **Password protection** for privacy
- **Real-time synchronization**

### **📝 Personal Diary System**
- **AI-driven entries** via natural language
- **Manual editing** and deletion
- **Mood tracking** and reflection
- **Private thoughts** storage

### **🧠 Smart Memory System**
- **Persistent context** across sessions
- **Relationship insights** generation
- **Automatic feeling detection**
- **Communication pattern analysis**

## 🚀 Quick Start

### **Prerequisites**
```bash
python3.8+
pip3
```

### **Installation**
```bash
# Clone repository
git clone https://github.com/Personaz1/LOVE.git
cd LOVE

# Install dependencies
pip3 install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### **Environment Variables**
```bash
# Required
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key

# Optional (fallback)
OPENAI_API_KEY=your_openai_api_key
```

### **Launch**
```bash
# Web interface
python3 start_web.py

# Telegram bot
python3 start_bot.py
```

## 🔐 Access

### **Web Interface**
- **URL**: http://localhost:8000
- **Meranda**: username=meranda, password=musser
- **Stepan**: username=stepan, password=stepan

### **Telegram Bot**
- Start chat with your bot
- Send `/start` to begin

## 🏗️ Architecture

### **Core Components**
```
FAMILY/
├── ai_client.py          # AI model interface
├── web_app.py            # FastAPI web application
├── telegram_bot.py       # Telegram bot handler
├── memory/               # Persistent storage
│   ├── user_profiles.py  # User profile management
│   └── relationship_memory.py
├── prompts/              # AI prompt engineering
├── static/               # Web assets
└── templates/            # HTML templates
```

### **AI Integration**
- **Primary**: Google Gemini 2.5 Pro
- **Fallback**: OpenAI GPT models
- **Function calling** for profile updates
- **Response cleaning** for natural conversation

### **Data Storage**
- **JSON-based** persistent storage
- **User profiles** in individual files
- **Relationship context** in shared files
- **Diary entries** per user

## 🎨 UI Features

### **Themes**
- **Light theme** (default for Meranda)
- **Dark theme** (default for Stepan)
- **Romantic design** with hearts and gradients

### **Components**
- **Chat interface** with real-time messaging
- **Profile editor** with hidden profile access
- **Diary management** with AI integration
- **Responsive design** for all devices

## 🔧 Configuration

### **AI Models**
```python
# Primary: Gemini 2.5 Pro
GEMINI_MODEL = "gemini-2.0-flash-exp"

# Fallback: OpenAI
OPENAI_MODEL = "gpt-4"
```

### **User Management**
```python
# Default users
USERS = {
    "meranda": "musser",
    "stepan": "stepan"
}
```

## 📊 Monitoring

### **Logging**
- **Detailed logs** in `logs/bot.log`
- **Performance metrics** for AI calls
- **Error tracking** and debugging
- **User interaction** analytics

### **Health Checks**
- **API connectivity** monitoring
- **Memory usage** tracking
- **Response time** measurement
- **Error rate** analysis

## 🔒 Security

### **Data Protection**
- **Environment variables** for sensitive data
- **Password authentication** for web access
- **Local storage** for user data
- **No external data sharing**

### **Privacy Features**
- **Individual user isolation**
- **Hidden profile protection**
- **Secure API key handling**
- **Local-only data storage**

## 🚀 Deployment

### **Docker**
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

### **Manual Deployment**
```bash
# Production setup
pip3 install -r requirements.txt
python3 start_web.py --host 0.0.0.0 --port 8000
```

## 🤝 Contributing

### **Development Setup**
```bash
# Install development dependencies
pip3 install -r requirements-dev.txt

# Run tests
python3 -m pytest tests/

# Code formatting
black .
isort .
```

### **Project Structure**
- **Modular design** for easy extension
- **Type hints** for better code quality
- **Comprehensive logging** for debugging
- **Documentation** for all components

## 📈 Roadmap

### **Phase 1** ✅
- [x] Basic AI integration
- [x] Web interface
- [x] User profiles
- [x] Diary system

### **Phase 2** 🚧
- [ ] MCP server integration
- [ ] Advanced analytics
- [ ] Mobile app
- [ ] Voice interface

### **Phase 3** 📋
- [ ] Group therapy sessions
- [ ] Relationship milestones
- [ ] Integration with calendar
- [ ] Advanced AI insights

## 📄 License

**Private Project** - All rights reserved

## 🙏 Acknowledgments

- **Google Gemini** for AI capabilities
- **OpenAI** for fallback support
- **FastAPI** for web framework
- **python-telegram-bot** for Telegram integration

---

**💕 Built with love for couples who want to understand each other better**

*Dr. Harmony - Your personal relationship consultant* 