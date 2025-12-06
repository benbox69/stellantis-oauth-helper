#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
import urllib.request
import locale
import argparse

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QMessageBox,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, Qt
from urllib.parse import urlparse, parse_qs

LANG = None
# Allow enabling debug via environment variable STELLANTIS_DEBUG=1/true/yes
DEBUG = os.getenv("STELLANTIS_DEBUG", "f").lower()[0] in ["1", "t", "y"]

CONFIG_URL = "https://raw.githubusercontent.com/andreadegiovine/homeassistant-stellantis-vehicles/develop/custom_components/stellantis_vehicles/configs.json"

# Simple i18n mechanism with per-language string maps and a selector.
# Add more languages by extending STRINGS.
STRINGS = {
    "en": {
        "WINDOW_TITLE": "Brand and Country Selection",
        "BRAND_LABEL": "Choose the brand:",
        "COUNTRY_LABEL": "Choose the country:",
        "CONTINUE_BUTTON": "Continue",
        "OAUTH_POPUP_TITLE": "OAuth Code Retrieved",
        "COPY_BUTTON_TEXT": "Copy the code",
        "CONFIGS_DOWNLOADED": "Configurations downloaded: {}",
        "CONFIGS_ERROR": "Error downloading configurations: {}",
        "ERROR_TITLE": "Error",
        "ERROR_MESSAGE": "Failed to download configurations: {}",
        "NO_COUNTRIES_FOR_BRAND": "No countries available for brand: {}",
        "AUTH_URL_LOG": "Authentication URL: {}",
        "MISSING_KEY_LOG": "Error: Missing key - {}",
        "MISSING_KEY_TITLE": "Error",
        "MISSING_KEY_MESSAGE": "Missing configuration key: {}",
        "BROWSER_WINDOW_TITLE": "Stellantis Login",
        "OAUTH_CODE_LABEL": "OAuth Code:\n{}",
    },
    "fr": {
        "WINDOW_TITLE": "Sélection de la marque et du pays",
        "BRAND_LABEL": "Choisissez la marque :",
        "COUNTRY_LABEL": "Choisissez le pays :",
        "CONTINUE_BUTTON": "Continuer",
        "OAUTH_POPUP_TITLE": "Code OAuth récupéré",
        "COPY_BUTTON_TEXT": "Copier le code",
        "CONFIGS_DOWNLOADED": "Configurations téléchargées : {}",
        "CONFIGS_ERROR": "Erreur lors du téléchargement des configurations : {}",
        "ERROR_TITLE": "Erreur",
        "ERROR_MESSAGE": "Échec du téléchargement des configurations : {}",
        "NO_COUNTRIES_FOR_BRAND": "Aucun pays disponible pour la marque : {}",
        "AUTH_URL_LOG": "URL d'authentification : {}",
        "MISSING_KEY_LOG": "Erreur : clé manquante - {}",
        "MISSING_KEY_TITLE": "Erreur",
        "MISSING_KEY_MESSAGE": "Clé de configuration manquante : {}",
        "BROWSER_WINDOW_TITLE": "Connexion Stellantis",
        "OAUTH_CODE_LABEL": "Code OAuth :\n{}",
    },
}


def detect_language():
    """Detect a suitable language code avoiding deprecated getdefaultlocale().

    Order of detection:
    1. locale.setlocale + locale.getlocale()
    2. Environment variables: LC_ALL, LC_CTYPE, LANG
    3. Fallback 'en'
    Returns base language (e.g. 'en', 'fr').
    """
    try:
        # Initialise locale from environment ('' means user default)
        locale.setlocale(locale.LC_ALL, "")
    except Exception:
        pass
    lang_code = None
    try:
        lang_code = (locale.getlocale()[0] or "").strip()
    except Exception:
        lang_code = ""
    if not lang_code:
        for var in ("LC_ALL", "LC_CTYPE", "LANG"):
            val = os.environ.get(var, "").strip()
            if val:
                lang_code = val
                break
    if not lang_code:
        lang_code = "en"
    # Normalise separators and extract base
    base = lang_code.replace("-", "_").split("_")[0].lower()
    return base if base in STRINGS else "en"


# Initialise language if not already overridden later via CLI
if LANG is None:
    LANG = detect_language()


def t(key):
    return STRINGS.get(LANG, STRINGS["en"]).get(key, key)


def download_configs():
    try:
        with urllib.request.urlopen(CONFIG_URL) as response:
            data = json.loads(response.read().decode())
            if DEBUG:
                print(t("CONFIGS_DOWNLOADED").format(data))
            return data
    except Exception as e:
        print(t("CONFIGS_ERROR").format(e))
        QMessageBox.critical(None, t("ERROR_TITLE"), t("ERROR_MESSAGE").format(e))
        sys.exit(1)


class BrandCountrySelector(QWidget):
    def __init__(self, configs):
        super(BrandCountrySelector, self).__init__()
        self.configs = configs
        self.setWindowTitle(t("WINDOW_TITLE"))
        self.setGeometry(400, 300, 400, 200)

        self.layout = QVBoxLayout()

        self.brand_label = QLabel(t("BRAND_LABEL"))
        self.layout.addWidget(self.brand_label)

        self.brand_combo = QComboBox()
        self.valid_brands = [b for b in configs if "configs" in configs[b]]
        self.brand_combo.addItems(self.valid_brands)
        self.brand_combo.currentTextChanged.connect(self.update_countries)
        self.layout.addWidget(self.brand_combo)

        self.country_label = QLabel(t("COUNTRY_LABEL"))
        self.layout.addWidget(self.country_label)

        self.country_combo = QComboBox()
        self.layout.addWidget(self.country_combo)

        self.start_button = QPushButton(t("CONTINUE_BUTTON"))
        self.start_button.clicked.connect(self.launch_browser)
        self.layout.addWidget(self.start_button)

        self.setLayout(self.layout)
        self.update_countries(self.brand_combo.currentText())

    def update_countries(self, brand_name):
        self.country_combo.clear()
        try:
            countries = self.configs[brand_name]["configs"].keys()
            self.country_combo.addItems(sorted(countries))
            self.country_combo.setCurrentIndex(0)
        except KeyError:
            print(t("NO_COUNTRIES_FOR_BRAND").format(brand_name))
            self.country_combo.clear()

    def launch_browser(self):
        brand = self.brand_combo.currentText()
        country = self.country_combo.currentText()

        try:
            cfg = self.configs[brand]
            country_cfg = cfg["configs"][country]
            oauth_url = cfg["oauth_url"]
            scheme = cfg["scheme"]
            locale_code = country_cfg["locale"]
            client_id = country_cfg["client_id"]

            auth_url = (
                f"{oauth_url}/am/oauth2/authorize?client_id={client_id}&response_type=code"
                f"&redirect_uri={scheme}://oauth2redirect/{country.lower()}&scope=openid%20profile%20email&locale={locale_code}"
            )

            if DEBUG:
                print(t("AUTH_URL_LOG").format(auth_url))

            self.browser_window = OAuthBrowser(auth_url, scheme)
            self.browser_window.show()
            self.close()
        except KeyError as e:
            print(t("MISSING_KEY_LOG").format(e))
            QMessageBox.critical(
                self, t("MISSING_KEY_TITLE"), t("MISSING_KEY_MESSAGE").format(e)
            )


class CustomWebPage(QWebEnginePage):
    def __init__(self, scheme, parent=None):
        super(CustomWebPage, self).__init__(parent)
        self.scheme = scheme

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Suppress JS console output unless DEBUG enabled
        if DEBUG:
            try:
                level_name = {0: "Info", 1: "Warning", 2: "Error"}.get(
                    int(level), str(level)
                )
            except Exception:
                level_name = str(level)
            print(f"JS {level_name}: {message} (line {lineNumber})")
            # Call super for any internal handling if needed
            return super(CustomWebPage, self).javaScriptConsoleMessage(
                level, message, lineNumber, sourceID
            )
        # When not debugging, do nothing (suppress output)
        return

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        url_str = url.toString()
        if url_str.startswith("{}://".format(self.scheme)):
            parsed = urlparse(url_str)
            params = parse_qs(parsed.query)
            code = params.get("code", [""])[0]
            if DEBUG:
                print("=" * 20)
                print(t("OAUTH_CODE_LABEL").format(code))
                print("=" * 20)

            self.view().parent().show_oauth_popup(code)
            return False
        return super(CustomWebPage, self).acceptNavigationRequest(
            url, nav_type, is_main_frame
        )


class OAuthBrowser(QWidget):
    def __init__(self, auth_url, scheme):
        super(OAuthBrowser, self).__init__()
        self.setWindowTitle(t("BROWSER_WINDOW_TITLE"))
        self.setGeometry(300, 300, 900, 700)

        layout = QVBoxLayout(self)
        self.webview = QWebEngineView(self)
        self.page = CustomWebPage(scheme, self.webview)
        self.webview.setPage(self.page)
        layout.addWidget(self.webview)

        self.webview.load(QUrl(auth_url))

    def show_oauth_popup(self, code):
        self.popup = OAuthPopup(code)
        self.popup.show()
        self.close()


class OAuthPopup(QWidget):
    def __init__(self, code):
        super(OAuthPopup, self).__init__()
        self.setWindowTitle(t("OAUTH_POPUP_TITLE"))
        self.setGeometry(400, 400, 500, 100)

        layout = QVBoxLayout()
        self.label = QLabel(t("OAUTH_CODE_LABEL").format(code))
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.label)

        self.copy_button = QPushButton(t("COPY_BUTTON_TEXT"))
        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(code))
        layout.addWidget(self.copy_button)

        self.setLayout(layout)


if __name__ == "__main__":
    # Enable High DPI scaling for better appearance on 4K/HiDPI displays
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    # Allow pass-through rounding for precise scale factors
    try:
        from PyQt5.QtGui import QGuiApplication

        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--scale", type=float, help="UI scale factor (float > 0)")
    parser.add_argument(
        "--font-size", type=float, help="Explicit font size in points (> 0)"
    )
    parser.add_argument("--locale", type=str, help="Locale override (e.g. en, fr)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args, _ = parser.parse_known_args()

    scale_arg = args.scale if (args.scale or 0) > 0 else None
    font_size_arg = args.font_size if (args.font_size or 0) > 0 else None
    locale_arg = (args.locale or "").strip().lower() or None
    if args.debug:
        DEBUG = True

    # Apply locale override if provided; fallback to 'en' when unknown
    if locale_arg:
        try:
            base_locale = locale_arg.split("_")[0]
        except Exception:
            base_locale = locale_arg
        if base_locale in STRINGS:
            LANG = base_locale
        else:
            LANG = detect_language()

    configs = download_configs()

    app = QApplication(sys.argv)
    # Scale default font based on DPI (96dpi as baseline), with stronger boost on very high DPI
    try:
        screen = app.primaryScreen()
        dpi = screen.physicalDotsPerInch() if screen else 96
        if DEBUG:
            print(f"Screen DPI detected: {dpi}")
        scale = max(1.0, dpi / 96.0)
        # If extremely high DPI, add a comfort multiplier
        if dpi >= 150:
            scale *= 1.15
        if scale_arg is not None and scale_arg > 0:
            scale = scale_arg

        font = app.font()
        base_pt = font.pointSizeF() if font.pointSizeF() > 0 else 9.0
        if font_size_arg is not None and font_size_arg > 0:
            new_pt = font_size_arg
        else:
            new_pt = base_pt * scale
        # Ensure minimum comfortable size
        new_pt = max(new_pt, 11.0)
        font.setPointSizeF(new_pt)
        app.setFont(font)
    except Exception:
        pass

    selector = BrandCountrySelector(configs)
    selector.show()

    sys.exit(app.exec_())
