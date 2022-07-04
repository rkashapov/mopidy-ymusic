from mopidy.models import Image, Playlist, Ref

from mopidy_ymusic.playlist import WORLD_TOP_100


def test_library_root(library):
    assert library.root_directory == Ref.directory(uri='ymusic:directory:root', name='Yandex Music')


def test_browse(library, album, track, artist, tracks_event):
    album_event_ref, artist_event_ref, playlist_ref = library.browse(library.root_directory.uri)
    assert album_event_ref == Ref.directory(uri='ymusic:directory:event-0001', name='Album Event')
    assert artist_event_ref == Ref.directory(uri='ymusic:directory:event-0002', name='Artist Event')
    assert playlist_ref == Ref.playlist(uri=f'ymusic:playlist:event:{tracks_event.id}', name=tracks_event.title)

    [album_ref] = library.browse(album_event_ref.uri)
    assert album_ref == Ref.album(uri=f'ymusic:album:{album.id}', name=album.title)

    [track_ref] = library.browse(album_ref.uri)
    assert track_ref == Ref.track(uri=f'ymusic:track:{track.id}', name=track.title)

    [artist_ref] = library.browse(artist_event_ref.uri)
    assert artist_ref == Ref.artist(uri=f'ymusic:artist:{artist.id}', name=artist.name)

    [track_ref] = library.browse(artist_ref.uri)
    assert track_ref == Ref.track(uri=f'ymusic:track:{track.id}', name=track.title)


def test_lookup(library, mopidy_album, mopidy_artist, mopidy_track):
    assert library.lookup(library.root_directory.uri) == []
    assert library.lookup(mopidy_artist.uri) == [mopidy_track]
    assert library.lookup(mopidy_album.uri) == [mopidy_track]
    assert library.lookup(mopidy_track.uri) == [mopidy_track]


def test_search(library, client, mopidy_album, mopidy_artist, mopidy_track):
    def assert_result(result):
        assert result.uri == 'ymusic:search'
        assert result.albums == (mopidy_album,)
        assert result.artists == (mopidy_artist,)
        assert result.tracks == (mopidy_track,)

    result = library.search({'any': ['AnyText']}, [])
    client.search.assert_called_with('AnyText', type_='all')
    assert_result(result)

    result = library.search({'artist': ['Artist']}, [])
    client.search.assert_called_with('Artist', type_='artist')
    assert_result(result)

    result = library.search({'album': ['Album']}, [])
    client.search.assert_called_with('Album', type_='album')
    assert_result(result)

    result = library.search({'track': ['Track']}, [])
    client.search.assert_called_with('Track', type_='track')
    assert_result(result)

    client.search.reset_mock()
    result = library.search({'foobar': ['Unexpected']}, [])
    client.search.assert_not_called()
    assert result.albums == ()
    assert result.tracks == ()
    assert result.artists == ()


def event_as_playlist_uri(event):
    return f'ymusic:playlist:event:{event.id}'


def test_get_images(library, mopidy_artist, mopidy_album, mopidy_track, mopidy_playlist, tracks_event):
    event_uri = event_as_playlist_uri(tracks_event)
    images = library.get_images([
        mopidy_artist.uri,
        mopidy_album.uri,
        mopidy_track.uri,
        mopidy_playlist.uri,
        WORLD_TOP_100.uri,
        event_uri,
    ])
    assert images[mopidy_artist.uri] == [Image(uri='https://images.com/artist/cover.jpg?size=400x400')]
    assert images[mopidy_album.uri] == [Image(uri='https://images.com/album/cover.jpg?size=400x400')]
    assert images[mopidy_track.uri] == [Image(uri='https://images.com/track/cover.jpg?size=400x400')]
    # playlists
    assert images[mopidy_playlist.uri] == [Image(uri='https://images.com/playlist/cover.jpg?size=400x400')]
    assert images[WORLD_TOP_100.uri] == [Image(uri='https://images.com/playlist/cover.jpg?size=400x400')]
    assert images[event_uri] == [Image(uri='https://images.com/track/cover.jpg?size=400x400')]


def test_playback(playback, client, track, mopidy_track):
    assert playback.translate_uri(mopidy_track.uri) == 'https://server.com/track/128/mp3'
    client.tracks_download_info.assert_called_with(track.id, get_direct_links=True)


def test_playlists_as_list(playlists):
    assert playlists.as_list() == [WORLD_TOP_100]


def test_playlists_get_items(playlists, mopidy_playlist, mopidy_track, tracks_event):
    [track_ref] = playlists.get_items(mopidy_playlist.uri)
    assert track_ref == Ref.track(uri=mopidy_track.uri, name=mopidy_track.name)

    [track_ref] = playlists.get_items(event_as_playlist_uri(tracks_event))
    assert track_ref == Ref.track(uri=mopidy_track.uri, name=mopidy_track.name)

    [track_ref] = playlists.get_items(WORLD_TOP_100.uri)
    assert track_ref == Ref.track(uri=mopidy_track.uri, name=mopidy_track.name)


def test_playlists_lookup(playlists, mopidy_playlist, tracks_event, mopidy_track):
    assert playlists.lookup(mopidy_playlist.uri) == mopidy_playlist

    event_tracklist_uri = event_as_playlist_uri(tracks_event)
    assert playlists.lookup(event_tracklist_uri) == Playlist(
        uri=event_tracklist_uri,
        name=tracks_event.title,
        tracks=[mopidy_track],
    )

    assert playlists.lookup(WORLD_TOP_100.uri) == mopidy_playlist
