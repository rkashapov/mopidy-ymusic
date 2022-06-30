from mopidy.models import Image, Ref


def assert_refs_equal(one, two):
    assert one.type == two.type
    assert one.uri == two.uri
    assert one.name == two.name


def test_library_root(library):
    assert_refs_equal(library.root_directory, Ref.directory(uri='ymusic:directory:root', name='Yandex Music'))


def test_browse(library, album, track, artist):
    album_event_ref, artist_event_ref = library.browse(library.root_directory.uri)
    assert_refs_equal(album_event_ref, Ref.directory(uri='ymusic:directory:event-0001', name='Album Event'))
    assert_refs_equal(artist_event_ref, Ref.directory(uri='ymusic:directory:event-0002', name='Artist Event'))

    [album_ref] = library.browse(album_event_ref.uri)
    assert_refs_equal(album_ref, Ref.album(uri=f'ymusic:album:{album.id}', name=album.title))

    [track_ref] = library.browse(album_ref.uri)
    assert_refs_equal(track_ref, Ref.track(uri=f'ymusic:track:{track.id}', name=track.title))

    [artist_ref] = library.browse(artist_event_ref.uri)
    assert_refs_equal(artist_ref, Ref.artist(uri=f'ymusic:artist:{artist.id}', name=artist.name))

    [track_ref] = library.browse(artist_ref.uri)
    assert_refs_equal(track_ref, Ref.track(uri=f'ymusic:track:{track.id}', name=track.title))


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


def test_get_images(library, mopidy_artist, mopidy_album, mopidy_track):
    images = library.get_images([mopidy_artist.uri, mopidy_album.uri, mopidy_track.uri])
    assert images[mopidy_artist.uri] == [Image(uri='https://images.com/artist/cover.jpg?size=400x400')]
    assert images[mopidy_album.uri] == [Image(uri='https://images.com/album/cover.jpg?size=400x400')]
    assert images[mopidy_track.uri] == [Image(uri='https://images.com/track/cover.jpg?size=400x400')]


def test_playback(playback, client, track, mopidy_track):
    assert playback.translate_uri(mopidy_track.uri) == 'https://server.com/track/128/mp3'
    client.tracks_download_info.assert_called_with(track.id, get_direct_links=True)
