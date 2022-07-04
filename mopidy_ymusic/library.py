import functools
import logging

from mopidy.backend import LibraryProvider
from mopidy.models import Image, Ref, SearchResult

from .models import RefType, to_model, to_ref


logger = logging.getLogger(__name__)


ROOT_DIR = Ref.directory(uri=f'ymusic:{RefType.DIRECTORY.value}:root', name='Yandex Music')
ROOT_ARTWORK_URI = 'yastatic.net/doccenter/images/support.yandex.com/en/music/freeze/fzG5B6KxX0dggCpZn4SQBpnF4GA.png'


class YMusicLibraryProvider(LibraryProvider):

    root_directory = ROOT_DIR
    ignore_events = (
        'notification-not-logged-in',
        'notification-install-app',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._feed = None

    @property
    def feed(self):
        if self._feed is not None:
            return self._feed
        self._feed = self.backend.client.feed()
        return self._feed

    def get_feed_event(self, event_id):
        for event in self.feed.days[0].events:
            if event.id == event_id:
                return event

    @functools.lru_cache(maxsize=256)
    def browse(self, uri):
        logger.info(f'browse: {uri}')
        refs = []
        if uri == ROOT_DIR.uri:
            refs.extend(
                Ref.directory(uri=f'ymusic:{RefType.DIRECTORY.value}:{event.id}', name=event.title)
                if not event.tracks else Ref.playlist(uri=f'ymusic:playlist:event:{event.id}', name=event.title)
                for event in self.feed.days[0].events
                if event.id not in self.ignore_events
            )
            return refs

        _, ref_type, item_id = uri.split(':', 2)
        if ref_type == RefType.DIRECTORY.value:
            event = self.get_feed_event(item_id)
            refs.extend([
                *[to_ref(artist_event.artist) for artist_event in event.artists],
                *[to_ref(album_event.album) for album_event in event.albums],
            ])

        if ref_type == RefType.ALBUM.value:
            refs.extend(to_ref(track) for track in self._get_album_tracks(item_id))

        if ref_type == RefType.ARTIST.value:
            refs.extend(to_ref(track) for track in self._get_artist_tracks(item_id))

        return refs

    def _get_album_tracks(self, album_id):
        album = self.backend.client.albums_with_tracks(album_id)
        for volume in album.volumes:
            yield from volume

    def _get_artist_tracks(self, artist_id):
        return self.backend.client.artists_tracks(artist_id)

    def _get_tracks(self, track_id):
        return self.backend.client.tracks(track_id)

    @functools.lru_cache(maxsize=256)
    def lookup(self, uri):
        logger.info(f'library.lookup: {uri}')
        items = []
        _, ref_type, item_id = uri.split(':', 2)

        if ref_type == RefType.TRACK.value:
            items.extend(to_model(track) for track in self._get_tracks(item_id))

        elif ref_type == RefType.ALBUM.value:
            items.extend(to_model(track) for track in self._get_album_tracks(item_id))

        elif ref_type == RefType.ARTIST.value:
            items.extend(to_model(track) for track in self._get_artist_tracks(item_id))
        return items

    def search(self, query, uris, exact=False):
        logger.info(f'search: {query}')
        search_type = 'all'
        text = ''
        if 'any' in query:
            text = ' '.join(query['any'])
            search_type = 'all'
        if 'artist' in query:
            text = ' '.join(query['artist'])
            search_type = 'artist'
        if 'album' in query:
            text = ' '.join(query['album'])
            search_type = 'album'
        if 'track' in query:
            text = ' '.join(query['track'])
            search_type = 'track'

        if not text:
            return SearchResult(uri='ymusic:search')

        albums = []
        search_result = self.backend.client.search(text, type_=search_type)
        if search_result.albums:
            albums = [to_model(album) for album in search_result.albums.results]
        artists = []
        if search_result.artists:
            artists = [to_model(artist) for artist in search_result.artists.results]
        tracks = []
        if search_result.tracks:
            tracks = [to_model(track) for track in search_result.tracks.results]
        return SearchResult(uri='ymusic:search', albums=albums, artists=artists, tracks=tracks)

    def get_images(self, uris):
        logger.info(f'images: {uris}')
        images = {}
        for uri in uris:
            artwork = ''
            _, ref_type, item_id = uri.split(':', 2)
            if ref_type == RefType.DIRECTORY.value:
                if item_id == 'root':
                    artwork = ROOT_ARTWORK_URI
                else:
                    event = self.get_feed_event(item_id)
                    if event.type == 'artists':
                        artwork = event.artists[0].artist.cover.uri
                    elif event.type == 'tracks':
                        artwork = event.tracks[0].cover_uri
                    elif event.type == 'albums':
                        artwork = event.albums[0].album.cover_uri

            elif ref_type == RefType.TRACK.value:
                track = self.backend.client.tracks(item_id)[0]
                artwork = track.cover_uri

            elif ref_type == RefType.ALBUM.value:
                album = self.backend.client.albums(item_id)[0]
                artwork = album.cover_uri

            elif ref_type == RefType.ARTIST.value:
                artist = self.backend.client.artists(item_id)[0]
                artwork = artist.cover.uri

            elif ref_type == RefType.PLAYLIST.value:
                playlist = None
                if item_id.startswith('event'):
                    _, event_id = item_id.split(':', 1)
                    event = self.get_feed_event(event_id)
                    if event.tracks:
                        artwork = event.tracks[0].cover_uri
                elif item_id in self.backend.playlists.chart_types:
                    playlist = self.backend.client.chart(item_id).chart
                else:
                    playlist = self.backend.client.playlists_list([item_id])[0]
                if playlist:
                    artwork = playlist.cover.uri

            if artwork:
                artwork_uri = f'https://{artwork.replace("%%", "400x400")}'
                images[uri] = [Image(uri=artwork_uri)]

        return images
