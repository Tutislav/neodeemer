from locale import getdefaultlocale

from kivy.utils import platform


CZ = {
    #common
    "Added to download queue": "Přidáno do fronty stahování",
    "Download completed": "Stahování dokončeno",
    "Downloaded ": "Staženo ",
    " songs": " skladeb",
    "Error while playing track": "Chyba při přehrávání skladby",
    #navigation_menu
    "Spotify search": "Vyhledávání na Spotify",
    "Saved songs will have tags": "Hudba se zařadí do alb",
    "YouTube search": "Vyhledávání na YouTube",
    "Saved songs won't have tags": "Hudba se nezařadí do alb",
    "Spotify playlist": "Spotify playlist",
    "YouTube playlist": "YouTube playlist",
    "Settings": "Nastavení",
    #SpotifyScreen
    "[b]Artists[/b]": "[b]Interpreti[/b]",
    "[b]Albums[/b]": "[b]Alba[/b]",
    "[b]Tracks[/b]": "[b]Skladby[/b]",
    "Search singers/bands": "Vyhledávání zpěváků/kapel",
    "Search albums": "Vyhledávání alb",
    "Search tracks": "Vyhledávání skladeb",
    #YouTubeScreen
    "Search video name": "Vyhledávání videí",
    #SPlaylistScreen
    "Link or ID of Spotify playlist": "Odkaz na Spotify playlist",
    #YPlaylistScreen
    "Link of YouTube playlist": "Odkaz na YouTube playlist",
    #tracks_actions
    "Cancel": "Zrušit",
    "All": "Všechny",
    "Only selected": "Jen vybrané",
    #playlist_actions
    "Show": "Zobrazit",
    #SettingsScreen
    "Create subfolders": "Vytvářet podsložky",
    "Music folder": "Složka, do které se ukládá hudba",
    "Choose folder": "Vybrat složku",
    "Toggle theme": "Přepnout vzhled",
    "Language": "Jazyk",
    "Settings saved": "Nastavení uloženo",
    #submit_bug_dialog
    "Submit bug": "Nahlásit chybu",
    "If some tracks has bad quality or even doesn't match the name you can submit it": "Pokud je nějaká skladba ve špatné kvalitě nebo dokonce nesedí ke jménu skladby, tak ji můžete nahlásit"
}

class Localization():
    TITLE = "Neodeemer"
    LANGUAGES = {
        "en_US": "default",
        "cs_CZ": CZ
    }

    def __init__(self):
        self.lang = "en-US"
        if platform == "android":
            from jnius import autoclass
            javalocale = autoclass("java.util.Locale")
            self.system_lang = javalocale.getDefault().toString()
        else:
            self.system_lang = getdefaultlocale()[0]
        for lang in self.LANGUAGES.keys():
            if lang == self.system_lang:
                self.lang = self.system_lang
    
    def set_lang(self, lang):
        self.lang = lang
    
    def get_lang(self):
        return self.lang
    
    def get_market(self):
        return self.system_lang[-2:]
    
    def get(self, text):
        if self.lang == "en_US":
            return text
        else:
            return self.LANGUAGES[self.lang][text]