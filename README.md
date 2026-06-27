# 🦉 DuolingoCLI

> Practice Duolingo lessons directly from your terminal with a beautiful CLI interface.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg)

## ⚠️ Disclaimer

This is an **unofficial** tool that uses reverse-engineered Duolingo API endpoints. It is **not** affiliated with or endorsed by Duolingo. Use at your own risk — automated API usage may violate Duolingo's Terms of Service.

**Recommendations:**
- Using it for your own language learning via interactive practice should be fine, but proceed with caution.
- Don't spam the API with rapid automated scripts.
- This tool adds natural delays between API requests.

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/DuolingoCLI.git
cd DuolingoCLI

# Install the CLI tool
pip install -e .
```

> **Note:** To enable audio playback, `playsound` is required and installed by default.

## 🔑 Authentication

DuolingoCLI uses a JWT token from your browser for authentication. This avoids CAPTCHA issues.

### Getting your JWT token:

1. Log in to [duolingo.com](https://www.duolingo.com) in your browser.
2. Open Developer Tools (`F12`).
3. Go to the **Console** tab.
4. Paste this command and hit Enter:
   ```javascript
   document.cookie.split(';').find(c => c.includes('jwt_token'))?.split('=')[1]
   ```
5. Copy the token value.

### Saving your token:

```bash
duo auth login
# Paste your token when prompted (input is hidden)
```

## 📖 Commands

### Core Learning
```bash
duo path                     # 🗺️ Continue your learning path (next lesson)
duo path --audio             # 🗺️ Play lesson audio out loud
duo practice                 # 🦉 Start general global practice
duo practice --audio         # 🦉 Start practice with audio enabled
duo practice --type listen   # 👂 Listening-focused practice
duo practice --type speak    # 🗣️ Speaking-focused practice
```

### Profile & Stats
```bash
duo profile                  # 👤 View your full profile and courses
duo stats                    # 📊 View advanced dashboard (Total XP, Active Courses, Streak)
duo streak                   # 🔥 View streak details
duo leaderboard              # 🏆 View your weekly leaderboard
duo health                   # ❤️ View your current hearts/health
duo shop                     # 🛒 View the store and your gem balance
```

### Authentication
```bash
duo auth status              # Check if you're currently logged in
duo auth logout              # Remove saved token
```

## 🎮 Practice Experience

The CLI brings a beautiful, fully functional terminal UI to your language learning:
- **Audio Support:** Add the `--audio` flag to download and play TTS audio for listening exercises.
- **Health Tracking:** Lose hearts dynamically on mistakes, just like the real app.
- **Interactive Prompts:** Pick words, match pairs, translate sentences, and type what you hear.

## 🏗️ Project Structure

```
DuolingoCLI/
├── pyproject.toml              # Project config & dependencies
├── README.md                   # This file
└── src/
    └── duolingo_cli/
        ├── main.py             # CLI commands (click)
        ├── api.py              # Duolingo API client
        ├── config.py           # Token & config management
        ├── ui.py               # Rich terminal UI rendering
        └── practice.py         # Interactive practice loop & challenges
```

## 📝 License

MIT — Use responsibly.
