# stellantis-oauth-helper

A simple Python GUI tool to assist with the OAuth2 authorization flow for Stellantis services (MyPeugeot, MyCitroën, MyDS, MyOpel and MyVauxhall).

This tool dynamically fetches the latest configuration from the [Home Assistant Stellantis integration](https://github.com/andreadegiovine/homeassistant-stellantis-vehicles), and allows users to easily retrieve the OAuth2 authorization code without manual browser inspection.

## ✨ Features

- ✅ Automatically downloads the latest Stellantis brand/country configurations  
- ✅ Supports multiple brands and locales  
- ✅ Simple UI for selecting brand and country  
- ✅ Embedded browser for authentication  
- ✅ Automatically intercepts redirect and extracts the OAuth2 `code`  
- ✅ One-click copy of the authorization code  
- ✅ Languages supported: French, English  

## ⚙️ Prerequisites

- Python 3.7 or higher  
- Required Python packages: PyQt5, PyQtWebEngine (see [requirements.txt](requirements.txt))

## 🚀 How to Use

### 1. Clone the Repository

```bash
git clone https://github.com/benbox69/stellantis-oauth-helper.git
cd stellantis-oauth-helper
```

### 2. Run the Virtual Environment and Install Dependencies

```bash
python -m venv .venv

# Activate in Command Prompt
.venv\Scripts\activate.bat
# Activate in Linux/MacOS Bash
source .venv/bin/activate

python -m pip install -r requirements.txt
```

### 3. Run the Application

```bash
python oauth_helper.py
# available switches:
# --locale fr|en (auto detects by default)
# --debug
# --scale F (where F is a float for the UI scaling factor - try 2.5)
# --font-size I (where I is an int for the font size - try 16)
```

## 🖥️ Application Flow

1. The application automatically downloads the `configs.json` file used by the [Home Assistant Stellantis integration](https://github.com/andreadegiovine/homeassistant-stellantis-vehicles).
2. A graphical window opens where you select your **brand** (e.g., MyPeugeot) and **country**.
3. Click **Continue** to launch the embedded browser.
4. Log in using your Stellantis account.
5. Once redirected, the application will:
   - Intercept the redirect,
   - Extract the OAuth2 `code`,
   - Display the code in a popup window with a **Copy** button.

## 📦 Next Steps

Once you have the code, you can:

- Use it with the [Home Assistant Stellantis integration](https://github.com/andreadegiovine/homeassistant-stellantis-vehicles)
- Or exchange it manually for an `access_token` / `refresh_token` via Stellantis token endpoint (not yet included in this tool — coming soon)

## 🛠️ Roadmap

- [ ] Exchange of `code` for `access_token` and `refresh_token`
- [ ] Option to save tokens to file
- [ ] Optional CLI/headless mode

## 📄 License

MIT License

