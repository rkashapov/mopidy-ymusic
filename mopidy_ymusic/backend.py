from mopidy.backend import Backend
from pykka import ThreadingActor
from yandex_music import Client

from .library import YMusicLibraryProvider
from .playback import YMusicPlaybackProvider
from .playlist import YMusicPlaylistsProvider


class YMusicBackend(ThreadingActor, Backend):
    uri_schemes = ['ymusic']

    def __init__(self, config, audio):
        super().__init__()
        self.audio = audio
        self.library = YMusicLibraryProvider(self)
        self.playback = YMusicPlaybackProvider(audio, self)
        self.playlists = YMusicPlaylistsProvider(self)
        self.client = Client(config['ymusic']['token'])
        self.config = config

    def on_start(self):
        self.client.init()
