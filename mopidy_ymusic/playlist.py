import logging
from functools import lru_cache

from mopidy.backend import PlaylistsProvider
from mopidy.models import Playlist, Ref

from .models import to_model


logger = logging.getLogger(__name__)


WORLD_TOP_100 = Ref.playlist(uri='ymusic:playlist:world', name='World Top 100')


class YMusicPlaylistsProvider(PlaylistsProvider):
    chart_types = ('world',)

    def as_list(self):
        result = [WORLD_TOP_100]
        return result

    @lru_cache(maxsize=64)
    def get(self, playlist_id) -> Playlist:
        if playlist_id.startswith('event'):
            _, event_id = playlist_id.split(':', 1)
            event = self.backend.library.get_feed_event(event_id)
            tracks = [to_model(track) for track in event.tracks]
            return Playlist(
                uri=f'ymusic:playlist:event:{event_id}',
                name=event.title,
                tracks=tracks,
            )

        if playlist_id in self.chart_types:
            playlist = self.backend.client.chart(playlist_id).chart
        else:
            playlist = self.backend.client.playlists_list([playlist_id])[0]

        return to_model(playlist)

    def get_items(self, uri):
        _, ref_type, playlist_id = uri.split(':', 2)
        if ref_type != 'playlist':
            return None

        playlist = self.get(playlist_id)
        return [Ref.track(uri=track.uri, name=track.name) for track in playlist.tracks]

    def lookup(self, uri):
        logger.info(f'playlists.lookup: {uri}')
        _, ref_type, playlist_id = uri.split(':', 2)
        if ref_type != 'playlist':
            return None
        return self.get(playlist_id)
