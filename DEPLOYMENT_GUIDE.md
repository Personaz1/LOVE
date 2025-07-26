# 🚀 Quick Deployment Guide

## For Meranda's Birthday Gift - Immediate Setup

### Step 1: Get Your Tokens
1. **Telegram Bot Token**: Message @BotFather on Telegram
   - Send `/newbot`
   - Name: "Dr. Harmony"
   - Username: "dr_harmony_bot" (or similar)
   - Copy the token

2. **Gemini API Key**: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create account if needed
   - Generate new API key
   - Copy the key
   - **Model**: Gemini 2.5 Pro (state-of-the-art for complex reasoning)

### Step 2: Quick Local Setup
```bash
# Clone or download the project
cd FAMILY

# Run setup script
./scripts/setup.sh

# Edit environment file
nano .env
# Add your tokens:
# TELEGRAM_BOT_TOKEN=your_telegram_token_here
# GEMINI_API_KEY=your_gemini_key_here

# Start the bot
./scripts/dev.sh
```

### Step 3: Test the Bot
1. Open Telegram
2. Find your bot (@dr_harmony_bot)
3. Send `/start`
4. Follow the setup process
5. Start chatting!

## For VPS Deployment (Future)

### Step 1: Server Setup
```bash
# SSH into your VPS
ssh user@your-vps-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Logout and login again
exit
ssh user@your-vps-ip
```

### Step 2: Deploy Bot
```bash
# Clone project
git clone <your-repo-url>
cd family-psychologist-bot

# Configure environment
cp env.example .env
nano .env  # Add your tokens (TELEGRAM_BOT_TOKEN, GEMINI_API_KEY)

# Deploy
./scripts/deploy.sh
```

### Step 3: Monitor
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f family-psychologist-bot

# Update bot
git pull
docker-compose up -d --build
```

## Bot Features for Stepan & Meranda

### 🌟 What the Bot Does
- **Remembers Everything**: All conversations and relationship history
- **Smart Analysis**: Identifies communication patterns and emotional trends
- **Conflict Mediation**: Helps resolve disagreements constructively
- **Milestone Celebration**: Records and celebrates positive moments
- **Personalized Advice**: Adapts to your relationship phase and style
- **User Profiles**: Individual personality and relationship characteristics
- **Personal Diaries**: Private reflection and emotional tracking
- **Customized Insights**: Tailored advice based on your unique profile

### 🎯 Key Commands
- `/start` - Welcome and setup
- `/setup` - Configure relationship profile
- `/insights` - View relationship analysis
- `/conflict` - Guided conflict resolution
- `/milestone` - Record positive moments
- `/help` - Show all commands

### 💕 Perfect Gift Features
- **Private & Secure**: All data stays between Stepan and Meranda
- **Always Available**: 24/7 relationship support
- **Growing Intelligence**: Learns from your interactions
- **Professional Quality**: Based on relationship psychology research
- **Personal Touch**: Adapts to your unique relationship dynamics
- **Individual Profiles**: Separate personality and growth tracking for each partner
- **Personal Diaries**: Private space for individual thoughts and feelings
- **Customized Advice**: Specific recommendations based on your communication style and love language

## Customization Options

### Change Bot Personality
Edit `prompts/psychologist_prompt.py` to modify:
- Communication style
- Response tone
- Specialization focus
- Interaction patterns

### Add New Features
- New commands in `bot/family_psychologist_bot.py`
- Additional memory types in `memory/relationship_memory.py`
- Custom MCP tools in `mcp_tools/mcp_client.py`

### Integrate MCP Server
When you get your MCP server:
1. Add MCP server URL to `.env`
2. Bot will automatically use advanced memory features
3. Enhanced pattern analysis and external resources

## Troubleshooting

### Common Issues
1. **Bot not responding**: Check logs with `docker-compose logs`
2. **API errors**: Verify OpenAI API key and credits
3. **Memory issues**: Check disk space and file permissions
4. **Network problems**: Verify internet connection and firewall settings

### Getting Help
- Check logs: `docker-compose logs -f`
- Test locally: `./scripts/dev.sh`
- Run tests: `./scripts/test.sh`
- Check configuration: Verify `.env` file

## Next Steps

### For Meranda's Gift
1. **Immediate**: Set up locally and test
2. **Short-term**: Deploy to VPS for 24/7 availability
3. **Long-term**: Integrate MCP server for advanced features

### For Future Couples
- **Multi-tenant**: Support multiple couples
- **Advanced Analytics**: Deep relationship insights
- **Integration APIs**: Calendar, reminders, goal tracking
- **Research Integration**: Latest psychology findings

---

**Dr. Harmony** - Your AI relationship companion, ready to strengthen bonds and build lasting love! 💕

*Built with love for Stepan & Meranda and all couples seeking deeper connection.* 