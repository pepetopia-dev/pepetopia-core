# 🐸 Pepetopia Bot (TOPI) Core

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-blue)
![AI](https://img.shields.io/badge/AI-Powered-green)
![License](https://img.shields.io/badge/License-MIT-orange)

**TOPI** is an advanced, AI-powered Telegram bot designed to protect, entertain, and inform crypto communities. Built specifically for the **Pepetopia** ecosystem on Solana, it serves as a Guardian, a Market Analyst, and a witty AI Companion.

---

## 🚀 Features

### 🛡️ **Fortress Security System**

- **Gatekeeper:** Automatically mutes new members upon entry.
- **Captcha Verification:** Users must click a "Verify" button to prove they are human.
- **Anti-Flood:** Mutes users who spam messages (default: 5 msgs/10s).
- **Anti-Link:** Blocks unauthorized links (Admins & Whitelist bypassed).
- **Profanity Filter:** Auto-deletes messages containing blacklisted words (scam, rug, fake, etc.).
- **Panic Mode:** Admin commands (`/lockdown`, `/unlock`) to freeze the chat during raids.

### 🤖 **AI Companion (Gemini Powered)**

- **Persona:** TOPI is an energetic, witty, and loyal crypto mascot.
- **Context Aware:** Understands crypto slang (WAGMI, HODL, LFG).
- **Multi-Mode:** Can roast portfolios, explain market trends, or generate hype tweets.
- **Interaction:** Responds to mentions (`@BotName`), replies, and DMs.

### 📊 **Market & Utility Tools**

- **Live Price:** Fetches real-time data from AscendEX (`/price`).
- **Contract Address:** Easy-to-copy CA command (`/ca`).
- **Socials:** Inline buttons for official links (`/socials`).
- **Autopilot:** Scheduled news digests, Fear & Greed index updates, and Top Gainers lists.

---

## 🛠️ Installation & Setup

Follow these steps to deploy your own instance of TOPI.

### Prerequisites

- Python 3.10 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Google Gemini API Key (Get it [here](https://aistudio.google.com/))

### 1. Clone the Repository

```bash
git clone [https://github.com/pepetopia-dev/pepetopia-core.git](https://github.com/pepetopia-dev/pepetopia-core.git)
cd pepetopia-core/telegram_bot
```

### 2. Create Virtual Environment

python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

### 3. Install Dependencies

pip install -r requirements.txt

### 4. Configuration

# telegram_bot/.env

ENVIRONMENT=development
TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
TRADING_SYMBOL=PEPETOPIA/USDT

### 5. Run the Bot

python main.py

### 🎮 Commands

Public Commands

Command,Description
/start,Shows the main dashboard.
/help,Displays support info.
/price,"Live market stats (Price, Volume, Change)."
/ca,Shows the Contract Address (Copy-Paste friendly).
/socials,Official community links.

Admin Commands
Command,Description
/lockdown,🚨 Emergency: Locks the group (Admins only).
/unlock,✅ Restore: Unlocks the group.
/autopilot_on,Starts the automated news & market feed.
/autopilot_off,Stops the automated feed.

### 📂 Project Structure

telegram_bot/
├── src/
│ ├── core/ # Config and environment management
│ ├── handlers/ # Command processors (Basic, Crypto, AI, Security)
│ ├── services/ # External APIs (Gemini, AscendEX, News)
│ └── main.py # Entry point
├── .env # Secrets (Not committed)
├── requirements.txt # Python dependencies
└── README.md # Documentation

### 🤝 Contributing

We welcome contributions! Please fork the repository and submit a Pull Request.

1-Fork the Project

2-Create your Feature Branch (git checkout -b feature/AmazingFeature)

3-Commit your Changes (git commit -m 'Add some AmazingFeature')

4-Push to the Branch (git push origin feature/AmazingFeature)

5-Open a Pull Request

### 📄 License

Distributed under the MIT License. See LICENSE for more information.
Built with 💚 by the Pepetopia Dev Team.
