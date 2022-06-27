from mopidy.models import Ref


def test_backend(backend):
    seen = set()

    def walk(ref):
        assert ref.uri not in seen
        seen.add(ref.uri)
        uris = []
        refs = backend.library.browse(ref.uri)[:5]

        if ref.type != Ref.DIRECTORY:
            assert backend.library.lookup(ref.uri) != []

        if ref.type == Ref.TRACK:
            assert backend.playback.translate_uri(ref.uri)

        assert backend.library.get_images([ref.uri])

        for ref in refs:
            uris.append(ref.uri)
            uris.extend(walk(ref))

        return uris

    assert walk(backend.library.root_directory) != []
    search_result = backend.library.search({'any': ['Beatles - Yellow Submarine']}, [])
    assert len(search_result.tracks) > 0
