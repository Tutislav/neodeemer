from locale import getdefaultlocale

from kivy.utils import platform

from tools import font


CZ = {
    #common
    "Added to download queue": "Přidáno do fronty stahování",
    "Download completed": "Stahování dokončeno",
    "Downloaded ": "Staženo ",
    " songs": " skladeb",
    " songs can't be downloaded": " skladeb se nepodařilo stáhnout",
    "Error while loading artists": "Chyba při načítání interpretů",
    "Error while loading albums": "Chyba při načítání alb",
    "Error while loading tracks": "Chyba při načítání skladeb",
    "Error while loading playlist": "Chyba při načítání playlistu",
    "Error while playing track": "Chyba při přehrávání skladby",
    "Not available on YouTube": "Není na YouTube",
    "Video is age restricted on YouTube": "Video je omezeno věkem na YouTube",
    "Error while downloading": "Chyba při stahování",
    #navigation_menu
    "Spotify search": "Vyhledávání na Spotify",
    "Tracks, Albums and Artists": "Skladby, Alba a Interpreti",
    "YouTube search": "Vyhledávání na YouTube",
    "Videos": "Videa",
    "Spotify playlist": "Spotify playlist",
    "YouTube playlist": "YouTube playlist",
    "Settings": "Nastavení",
    "Update": "Aktualizace",
    "New version is available": "Je dostupná nová verze",
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
    "Lyrics only": "Pouze texty",
    #SettingsScreen
    "Format": "Formát",
    "(Better quality)": "(Lepší kvalita)",
    "(Slower download)": "(Pomalejší stahování)",
    "Download lyrics": "Stahovat texty",
    "Unsynchronized lyrics": "Nesynchronizované texty",
    "Synchronized lyrics": "Synchronizované texty",
    "Enable WebApi": "Povolit WebApi",
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
    TITLE_R = "Neodeemer"
    LANGUAGES = {
        "en_US": "default",
        "cs_CZ": CZ
    }

    def __init__(self):
        self.lang = "en_US"
        if platform == "android":
            from jnius import autoclass
            javalocale = autoclass("java.util.Locale")
            self.system_lang = javalocale.getDefault().toString()
        else:
            self.system_lang = getdefaultlocale()[0]
        for lang in self.LANGUAGES.keys():
            if lang == self.system_lang:
                self.lang = self.system_lang
        self.TITLE = self.get(self.TITLE_R)
    
    def set_lang(self, lang):
        self.lang = lang
    
    def get_lang(self):
        return self.lang
    
    def get_market(self):
        return self.system_lang[-2:]
    
    def get(self, text):
        return font(self.get_r(text))

    def get_r(self, text):
        if self.lang == "en_US":
            return text
        elif text in self.LANGUAGES[self.lang]:
            return self.LANGUAGES[self.lang][text]
        else:
            return text