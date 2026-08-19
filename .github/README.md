<p align="center">
  <img src="banner.jpg" alt="SenpaiXWaifu Banner">
</p>

<h1 align="center"><b>Senpai X Waifu</b></h1>

<p align="center">
  <a href="https://github.com/SenpaiLabs/SenpaiXWaifu">
    <img src="https://img.shields.io/github/repo-size/SenpaiLabs/SenpaiXWaifu?color=purple&logo=github&logoColor=green&label=Repo%20Size">
  </a>
  <a href="https://github.com/SenpaiLabs/SenpaiXWaifu/issues">
    <img src="https://img.shields.io/github/issues/SenpaiLabs/SenpaiXWaifu?color=purple&logo=github&logoColor=green&label=Issues">
  </a>
  <a href="https://github.com/SenpaiLabs/SenpaiXWaifu/network/members">
    <img src="https://img.shields.io/github/forks/SenpaiLabs/SenpaiXWaifu?color=purple&logo=github&logoColor=green&label=Forks">
  </a>
  <a href="https://github.com/SenpaiLabs/SenpaiXWaifu/stargazers">
    <img src="https://img.shields.io/github/stars/SenpaiLabs/SenpaiXWaifu?color=purple&logo=github&logoColor=green&label=Stars">
  </a>
  <br>
  <a href="https://t.me/Collect_em_support">
    <img src="https://img.shields.io/badge/Support%20Group-Blue?style=for-the-badge&logo=telegram">
  </a>
</p>

---

<p align="center">
  <b>SenpaiXWaifu</b> is an incredibly fast, modern, and open-source Telegram Character Catcher Bot written purely in <b>TypeScript</b> using the <b>Telegraf</b> framework and a modular architecture.<br>
  Catch your favorite husbandos and waifus, trade them, and build the ultimate harem!
</p>

---

## 🌟 Features
- ⚡ **Lightning Fast:** Fully asynchronous operations powered by Node.js and the official MongoDB driver.
- 🌍 **Multi-Language Support:** Easily switch between languages with robust JSON locales.
- 🎮 **Gamified Experience:** Spawn, guess, trade, and collect legendary characters.
- 🛠️ **Modular Architecture:** Clean `src/` folder structure inspired by industry standards.

## 🚀 Deployment

### Requirements
- Node.js v18+
- MongoDB Database URI
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Method: VPS (Recommended)
You can deploy this bot on any VPS (Ubuntu/Debian) efficiently using `npm`.

<details>
<summary><b>Click here to view Deployment Steps</b></summary>

```bash
# 1. Update your system
sudo apt-get update && sudo apt-get upgrade -y           

# 2. Install Node.js (v18 or higher)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 3. Clone the repository
git clone https://github.com/SenpaiLabs/SenpaiXWaifu 
cd SenpaiXWaifu

# 4. Install Dependencies
npm install

# 5. Configure your bot
cp .env.example .env
nano .env # Fill in your BOT_TOKEN, MONGO_URI, OWNER_ID, etc.

# 6. Build and Run the bot (using tmux or PM2)
sudo apt install tmux -y && tmux
npm run build
npm start
```
</details>

---

## 📚 Commands

| Command | Description | Access |
| :--- | :--- | :--- |
| `/guess`, `/protecc` | Catch a spawned character. | All Users |
| `/harem` | View your awesome collection. | All Users |
| `/trade` | Exchange characters with friends. | All Users |
| `/top`, `/leaderboard` | Global leaderboard of harem collectors. | All Users |
| `/upload` | Add new characters to the database. | Uploaders / Sudo |
| `/set_on`, `/set_off` | Toggle specific character rarities. | Sudo |
| `/changetime` | Change the character spawn frequency. | Sudo |
| `/broadcast` | Broadcast messages to users and groups. | Sudo |
| `/ping` | Check if the bot is alive. | All Users |

---

<p align="center">
  <b>Developed with ❤️ by SenpaiLabs</b><br>
  <a href="https://github.com/SenpaiLabs/SenpaiXWaifu/blob/main/LICENSE">MIT License</a>
</p>
