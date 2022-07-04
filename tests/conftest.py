from unittest import mock

import pytest
from mopidy.models import (
    Album as MopidyAlbum,
    Artist as MopidyArtist,
    Playlist as MopidyPlaylist,
    Track as MopidyTrack,
)
from yandex_music import (
    Album,
    AlbumEvent,
    Artist,
    ArtistEvent,
    ChartInfo,
    Cover,
    Day,
    DownloadInfo,
    Event,
    Feed,
    Playlist,
    Search,
    SearchResult,
    Track,
    TrackShort,
)

from mopidy_ymusic.backend import YMusicBackend
from mopidy_ymusic.playlist import YMusicPlaylistsProvider


@pytest.fixture
def config():
    return {'ymusic': {'token': '', 'bitrate': 128}}


@pytest.fixture
def artist():
    return Artist(id='artist-0001', name='Artist 01 Name', cover=Cover(uri='images.com/artist/cover.jpg?size=%%'))


@pytest.fixture
def album(artist):
    return Album(
        id='album-0001',
        title='Album 01 Title',
        artists=[artist],
        cover_uri='images.com/album/cover.jpg?size=%%',
    )


@pytest.fixture
def track(album, artist):
    return Track(
        id='track-0001',
        title='Track 01 Title',
        artists=[artist],
        albums=[album],
        duration_ms=100500,
        cover_uri='images.com/track/cover.jpg?size=%%',
    )


@pytest.fixture
def playlist(track):
    return Playlist(
        uid='playlist-0001',
        title='A Playlist 01',
        tracks=[TrackShort(id=track.id, timestamp='', track=track)],
        cover=Cover(uri='images.com/playlist/cover.jpg?size=%%'),
        owner=None,
        made_for=None,
        play_counter=None,
        playlist_absence=None,
    )


@pytest.fixture
def mopidy_artist(artist):
    return MopidyArtist(uri=f'ymusic:artist:{artist.id}', name=artist.name, sortname=artist.name)


@pytest.fixture
def mopidy_album(mopidy_artist, album):
    return MopidyAlbum(uri=f'ymusic:album:{album.id}', name=album.title, artists=[mopidy_artist])


@pytest.fixture
def mopidy_track(mopidy_album, mopidy_artist, track):
    return MopidyTrack(
        uri=f'ymusic:track:{track.id}',
        name=track.title,
        length=track.duration_ms,
        album=mopidy_album,
        artists=[mopidy_artist],
    )


@pytest.fixture
def mopidy_playlist(mopidy_track, playlist):
    return MopidyPlaylist(
        uri=f'ymusic:playlist:{playlist.uid}',
        name=playlist.title,
        tracks=(mopidy_track,),
    )


@pytest.fixture
def tracks_event(track):
    return Event(
        id='event-0003',
        type='tracks',
        title='Tracks Event',
        albums=[],
        artists=[],
        tracks=[track],
    )


@pytest.fixture
def chart(playlist):
    return ChartInfo(
        chart=playlist,
        id='world',
        type=None,
        title=None,
        type_for_from='',
        menu=None,
    )


@pytest.fixture
def client(album, artist, track, playlist, tracks_event, chart):
    client = mock.Mock()
    client.feed.return_value = Feed(
        days=[
            Day(
                day='2022.06.30',
                tracks_to_play_with_ads=[],
                tracks_to_play=[],
                events=[
                    Event(
                        id='event-0001',
                        type='albums',
                        title='Album Event',
                        albums=[AlbumEvent(album=album, tracks=[])],
                        artists=[],
                        tracks=[],
                    ),
                    Event(
                        id='event-0002',
                        type='artists',
                        title='Artist Event',
                        albums=[],
                        artists=[ArtistEvent(
                            artist=artist,
                            tracks=[],
                            similar_to_artists_from_history=[],
                            subscribed=False,
                        )],
                        tracks=[],
                    ),
                    tracks_event,
                ],
            ),
        ],
        can_get_more_events=False,
        pumpkin=False,
        is_wizard_passed=False,
        generated_playlists=False,
        headlines=[],
        today='2022-06-30',
    )

    album.volumes = [[track]]
    client.albums_with_tracks.return_value = album
    client.artists_tracks.return_value = [track]
    client.tracks.return_value = [track]
    client.artists.return_value = [artist]
    client.albums.return_value = [album]
    client.search.return_value = Search(
        search_request_id='',
        text='',
        best=None,
        playlists=None,
        videos=None,
        users=None,
        podcasts=None,
        podcast_episodes=None,
        albums=SearchResult(results=[album], type='album', per_page=1, order=0, total=1),
        artists=SearchResult(results=[artist], type='artist', per_page=1, order=0, total=1),
        tracks=SearchResult(results=[track], type='track', per_page=1, order=0, total=1),
    )
    infos = [
        DownloadInfo(codec='aac', bitrate_in_kbps=128, gain=False, preview=False, download_info_url='', direct=True),
        DownloadInfo(codec='aac', bitrate_in_kbps=192, gain=False, preview=False, download_info_url='', direct=True),
        DownloadInfo(codec='mp3', bitrate_in_kbps=128, gain=False, preview=False, download_info_url='', direct=True),
        DownloadInfo(codec='mp3', bitrate_in_kbps=320, gain=False, preview=False, download_info_url='', direct=True),
    ]

    for info in infos:
        info.direct_link = f'https://server.com/track/{info.bitrate_in_kbps}/{info.codec}'

    client.tracks_download_info.return_value = infos
    client.playlists_list.return_value = [playlist]
    client.chart.return_value = chart
    return client


@pytest.fixture
def backend(config, client):
    backend = YMusicBackend(config, None)
    backend.client = client
    return backend


@pytest.fixture
def library(backend):
    return backend.library


@pytest.fixture
def playback(backend):
    return backend.playback


@pytest.fixture
def playlists(backend) -> YMusicPlaylistsProvider:
    return backend.playlists
