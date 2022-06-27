import enum
import functools

import yandex_music
from mopidy.backend import LibraryProvider
from mopidy.models import Album, Artist, Image, Ref, SearchResult, Track


class RefType(enum.Enum):
    DIRECTORY = 'directory'
    ALBUM = 'album'
    ARTIST = 'artist'
    TRACK = 'track'


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

    @functools.lru_cache(maxsize=256)
    def browse(self, uri):
        refs = []
        if uri == ROOT_DIR.uri:
            refs.extend(
                Ref.directory(uri=f'ymusic:{RefType.DIRECTORY.value}:{event.id}', name=event.title)
                for event in self.feed.days[0].events
                if event.id not in self.ignore_events
            )
            return refs

        _, ref_type, item_id = uri.split(':', 2)
        if ref_type == RefType.DIRECTORY.value:
            for event in self.feed.days[0].events:
                if event.id == item_id:
                    refs.extend([
                        *[to_ref(artist_event.artist) for artist_event in event.artists],
                        *[to_ref(album_event.album) for album_event in event.albums],
                        *[to_ref(track_event) for track_event in event.tracks],
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
        images = {}
        event_by_id = {event.id: event for event in self.feed.days[0].events}
        for uri in uris:
            artwork = ''
            _, ref_type, item_id = uri.split(':', 2)
            if ref_type == 'directory':
                if item_id == 'root':
                    artwork = ROOT_ARTWORK_URI
                else:
                    event = event_by_id[item_id]
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

            if artwork:
                artwork_uri = f'https://{artwork.replace("%%", "400x400")}'
                images[uri] = [Image(uri=artwork_uri)]

        return images


@functools.singledispatch
def to_model(obj: yandex_music.Album):
    return Album(
        uri=f'ymusic:{RefType.ALBUM.value}:{obj.id}',
        name=obj.title,
        artists=[to_model(artist) for artist in obj.artists],
    )


@to_model.register
def _(obj: yandex_music.Artist):
    return Artist(
        uri=f'ymusic:{RefType.ARTIST.value}:{obj.id}',
        name=obj.name,
        sortname=obj.name,
    )


@to_model.register
def _(obj: yandex_music.Track):
    return Track(
        uri=f'ymusic:{RefType.TRACK.value}:{obj.id}',
        name=obj.title,
        length=obj.duration_ms,
        artists=[to_model(artist) for artist in obj.artists],
        album=to_model(obj.albums[0]),
    )


@functools.singledispatch
def to_ref(obj: yandex_music.Album):
    return Ref.album(uri=f'ymusic:{RefType.ALBUM.value}:{obj.id}', name=obj.title)


@to_ref.register
def _(obj: yandex_music.Artist):
    return Ref.artist(uri=f'ymusic:{RefType.ARTIST.value}:{obj.id}', name=obj.name)


@to_ref.register
def _(obj: yandex_music.Track):
    return Ref.track(uri=f'ymusic:{RefType.TRACK.value}:{obj.id}', name=obj.title)
