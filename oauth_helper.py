# -*- coding: utf-8 -*-

import sys
import json
import urllib.request
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, Qt
from urllib.parse import urlparse, parse_qs

CONFIG_URL = "https://raw.githubusercontent.com/andreadegiovine/homeassistant-stellantis-vehicles/develop/custom_components/stellantis_vehicles/configs.json"

WINDOW_TITLE = "Brand and Country Selection"
BRAND_LABEL = "Choose the brand:"
COUNTRY_LABEL = "Choose the country:"
CONTINUE_BUTTON = "Continue"
OAUTH_POPUP_TITLE = "OAuth Code Retrieved"
COPY_BUTTON_TEXT = "Copy the code"

def download_configs():
    try:
        with urllib.request.urlopen(CONFIG_URL) as response:
            data = json.loads(response.read().decode())
            print("Configurations téléchargées : {}".format(data))
            return data
    except Exception as e:
        print("Erreur lors du téléchargement des configurations : {}".format(e))
        QMessageBox.critical(None, "Error", "Failed to download configurations: {}".format(e))
        sys.exit(1)

class BrandCountrySelector(QWidget):
    def __init__(self, configs):
        super(BrandCountrySelector, self).__init__()
        self.configs = configs
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(400, 300, 400, 200)

        self.layout = QVBoxLayout()

        self.brand_label = QLabel(BRAND_LABEL)
        self.layout.addWidget(self.brand_label)

        self.brand_combo = QComboBox()
        self.valid_brands = [b for b in configs if "configs" in configs[b]]
        self.brand_combo.addItems(self.valid_brands)
        self.brand_combo.currentTextChanged.connect(self.update_countries)
        self.layout.addWidget(self.brand_combo)

        self.country_label = QLabel(COUNTRY_LABEL)
        self.layout.addWidget(self.country_label)

        self.country_combo = QComboBox()
        self.layout.addWidget(self.country_combo)

        self.start_button = QPushButton(CONTINUE_BUTTON)
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
            print("No countries available for brand: {}".format(brand_name))
            self.country_combo.clear()

    def launch_browser(self):
        brand = self.brand_combo.currentText()
        country = self.country_combo.currentText()

        try:
            cfg = self.configs[brand]
            country_cfg = cfg["configs"][country]
            oauth_url = cfg["oauth_url"]
            scheme = cfg["scheme"]
            locale = country_cfg["locale"]
            client_id = country_cfg["client_id"]

            auth_url = "{}{}?client_id={}&response_type=code&redirect_uri={}://oauth2redirect/{}&scope=openid%20profile%20email&locale={}".format(
                oauth_url, "/am/oauth2/authorize", client_id, scheme, country.lower(), locale
            )

            print("Authentication URL: {}".format(auth_url))

            self.browser_window = OAuthBrowser(auth_url, scheme)
            self.browser_window.show()
            self.close()
        except KeyError as e:
            print("Error: Missing key - {}".format(e))
            QMessageBox.critical(self, "Error", "Missing configuration key: {}".format(e))

class CustomWebPage(QWebEnginePage):
    def __init__(self, scheme, parent=None):
        super(CustomWebPage, self).__init__(parent)
        self.scheme = scheme

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        url_str = url.toString()
        if url_str.startswith("{}://".format(self.scheme)):
            parsed = urlparse(url_str)
            params = parse_qs(parsed.query)
            code = params.get("code", [""])[0]

            self.view().parent().show_oauth_popup(code)
            return False
        return super(CustomWebPage, self).acceptNavigationRequest(url, nav_type, is_main_frame)

class OAuthBrowser(QWidget):
    def __init__(self, auth_url, scheme):
        super(OAuthBrowser, self).__init__()
        self.setWindowTitle("Connexion Stellantis")
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
        self.setWindowTitle(OAUTH_POPUP_TITLE)
        self.setGeometry(400, 400, 500, 100)

        layout = QVBoxLayout()
        self.label = QLabel("OAuth Code:\n{}".format(code))
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.label)

        self.copy_button = QPushButton(COPY_BUTTON_TEXT)
        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(code))
        layout.addWidget(self.copy_button)

        self.setLayout(layout)

if __name__ == "__main__":
    configs = download_configs()
    app = QApplication(sys.argv)
    selector = BrandCountrySelector(configs)
    selector.show()
    sys.exit(app.exec_())
