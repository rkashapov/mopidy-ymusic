import enum
import functools

import yandex_music
from mopidy.models import Album, Artist, Playlist, Ref, Track


class RefType(enum.Enum):
    DIRECTORY = 'directory'
    ALBUM = 'album'
    ARTIST = 'artist'
    TRACK = 'track'
    PLAYLIST = 'playlist'


@functools.singledispatch
def to_uri(obj: yandex_music.Album):
    return f'ymusic:{RefType.ALBUM.value}:{obj.id}'


@to_uri.register
def _(obj: yandex_music.Artist):
    return f'ymusic:{RefType.ARTIST.value}:{obj.id}'


@to_uri.register
def _(obj: yandex_music.Track):
    return f'ymusic:{RefType.TRACK.value}:{obj.id}'


@to_uri.register
def _(obj: yandex_music.Playlist):
    return f'ymusic:{RefType.PLAYLIST.value}:{obj.uid}'


@functools.singledispatch
def to_model(obj: yandex_music.Album):
    return Album(
        uri=to_uri(obj),
        name=obj.title,
        artists=[to_model(artist) for artist in obj.artists],
    )


@to_model.register
def _(obj: yandex_music.Artist):
    return Artist(
        uri=to_uri(obj),
        name=obj.name,
        sortname=obj.name,
    )


@to_model.register
def _(obj: yandex_music.Track):
    return Track(
        uri=to_uri(obj),
        name=obj.title,
        length=obj.duration_ms,
        artists=[to_model(artist) for artist in obj.artists],
        album=to_model(obj.albums[0]),
    )


@to_model.register
def _(obj: yandex_music.TrackShort):
    return to_model(obj.track)


@to_model.register
def _(obj: yandex_music.Playlist):
    return Playlist(uri=to_uri(obj), name=obj.title, tracks=[to_model(track) for track in obj.tracks])


@functools.singledispatch
def to_ref(obj: yandex_music.Album):
    return Ref.album(uri=to_uri(obj), name=obj.title)


@to_ref.register
def _(obj: yandex_music.Artist):
    return Ref.artist(uri=to_uri(obj), name=obj.name)


@to_ref.register
def _(obj: yandex_music.Track):
    return Ref.track(uri=to_uri(obj), name=obj.title)


@to_ref.register
def _(obj: yandex_music.Playlist):
    return Ref.playlist(uri=to_uri(obj), name=obj.title)


@to_ref.register
def _(obj: yandex_music.TrackShort):
    return to_ref(obj.track)
