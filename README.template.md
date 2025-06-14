# 📱 [InstaSave](https://t.me/igsavetgbot)

## User count: <USER_COUNT_PLACEHOLDER>

## 📈 User Growth

![User Chart](https://quickchart.io/chart?c=<CHART_CONFIG_PLACEHOLDER>)





A powerful Telegram bot that allows users to anonymously view Instagram Stories without logging into Instagram. Built with Python, aiogram, and Selenium for reliable story fetching and delivery.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-Latest-blue.svg)

## ✨ Features

- 🔍 **Anonymous Story Viewing** - View Instagram stories without logging in
- 🤖 **Telegram Integration** - Easy-to-use Telegram bot interface
- ⚡ **Automated Checking** - Set up automatic story checking with custom intervals
- 🖼️ **Media Support** - Handles both images and videos
- 👤 **Profile Information** - Shows user profile details and statistics
- 🔒 **Privacy Aware** - Respects private account limitations
- 📊 **User Settings** - Persistent user preferences and configurations
- 🛡️ **Error Handling** - Robust error handling and recovery mechanisms

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Chrome browser installed
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/kyemets/insta-save-telegram-bot.git
   cd instagram-story-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your bot token**
   Create a file named `tg_token.py`:
   ```python
   TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## 📋 Requirements

Create a `requirements.txt` file with these dependencies:

```
aiogram==2.25.1
aiohttp==3.8.5
selenium==4.15.0
webdriver-manager==4.0.1
```

## 🔧 Configuration

### Environment Variables

You can also use environment variables instead of `tg_token.py`:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

### Bot Settings

The bot automatically creates a `user_settings.json` file to store user preferences:

```json
{
  "user_id": {
    "auto_enabled": false,
    "interval": 3,
    "last_check": "2024-01-01T00:00:00",
    "target_username": "example_user"
  }
}
```

## 📖 Usage

### Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and bot introduction |
| `/story` | Request stories for a username |
| `/help` | Show all available commands |
| `/auto_on` | Enable automatic story checking |
| `/auto_off` | Disable automatic story checking |
| `/status` | Check your current settings |

### Basic Usage

1. **Start the bot**: Send `/start` to get started
2. **View stories**: Simply send an Instagram username (without @)
3. **Set auto-check**: Use `/auto_on` and select your preferred interval
4. **Get help**: Use `/help` for detailed command information

### Example Conversation

```
User: /start
Bot: 👋 Welcome to Instagram Stories Bot!
     🔍 Send me an Instagram username to view their stories anonymously.

User: johndoe
Bot: 🔎 Looking up @johndoe...
     🌐 Launching browser...
     ⌛ Fetching story data...
     📱 [Profile information with photo]
     📲 Found 3 stories. Sending...
     📖 [Story 1/3 - Image]
     📖 [Story 2/3 - Video]
     📖 [Story 3/3 - Image]
```

## 🏗️ Architecture

The bot is built with a modular architecture:

```
├── main.py                 # Main bot class and entry point
├── tg_token.py            # Bot token configuration
├── user_settings.json     # User preferences storage
├── bot.log               # Application logs
└── requirements.txt      # Python dependencies
```

### Core Components

- **`StoryBot`** - Main bot orchestrator
- **`SettingsManager`** - Handles user settings persistence
- **`BrowserManager`** - Manages Selenium browser operations
- **`APIClient`** - Handles API communication with retry logic
- **`AuthTokenManager`** - Generates authentication tokens
- **`URLDecoder`** - Decodes embedded media URLs

## 🛠️ Development

### Code Structure

The codebase follows professional Python development practices:

- **Type Hints** - Full type annotation coverage
- **Data Classes** - Clean data structures with `@dataclass`
- **Async/Await** - Proper asynchronous programming
- **Error Handling** - Comprehensive exception handling
- **Logging** - Structured logging with file and console output
- **Resource Management** - Proper cleanup with context managers

### Adding New Features

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Add tests** (if applicable)
5. **Commit your changes**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
6. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Running in Development Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

## 🐳 Docker Support

### Dockerfile

```dockerfile
FROM python:3.9-slim

# Install Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  instagram-bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    volumes:
      - ./user_settings.json:/app/user_settings.json
      - ./logs:/app/logs
    restart: unless-stopped
```

## 📊 Monitoring and Logs

The bot includes comprehensive logging:

- **File Logging** - All events logged to `bot.log`
- **Console Output** - Real-time status updates
- **Error Tracking** - Detailed error information
- **Performance Metrics** - API response times and success rates

### Log Levels

- **INFO** - General operations and status updates
- **WARNING** - Non-critical issues
- **ERROR** - Error conditions that need attention
- **DEBUG** - Detailed debugging information

## ⚠️ Limitations

- **Private Accounts** - Cannot access stories from private Instagram accounts
- **Rate Limits** - Subject to Instagram's rate limiting policies
- **Selenium Dependency** - Requires Chrome browser for web automation
- **No Authentication** - Does not require Instagram login (by design)

## 🔒 Privacy & Ethics

This bot is designed for legitimate use cases:

- ✅ **Viewing public content anonymously**
- ✅ **Educational and research purposes**
- ✅ **Personal use within Instagram's terms**

Please use responsibly and respect users' privacy.

## 🐛 Troubleshooting

### Common Issues

**Chrome Driver Issues**
```bash
# Update Chrome driver
pip install --upgrade webdriver-manager
```

**API Timeout Errors**
- Check your internet connection
- Verify the username exists and is public
- Try again after a few minutes

**Bot Not Responding**
- Check your bot token in `tg_token.py`
- Verify the bot is running without errors
- Check the logs in `bot.log`

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Guidelines

- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass

## 📞 Support

If you encounter any issues or have questions:

1. **Check the logs** - Look at `bot.log` for error details
2. **Review documentation** - Check this README and code comments
3. **Open an issue** - Create a GitHub issue with details
4. **Join discussions** - Participate in GitHub Discussions

## 🌟 Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Async Telegram Bot API framework
- [Selenium](https://selenium.dev/) - Web automation framework
- [aiohttp](https://aiohttp.readthedocs.io/) - Async HTTP client/server
- [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager) - Automatic WebDriver management

## 📈 Roadmap

- [ ] Web dashboard for bot management
- [ ] Scheduled story downloads
- [ ] Multi-user story comparison
- [ ] Story analytics and insights
- [ ] Integration with other social platforms
- [ ] Advanced filtering and search options

---

**⭐ If you find this project helpful, please consider giving it a star on GitHub!**
