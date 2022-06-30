import logging

from mopidy.backend import PlaybackProvider


logger = logging.getLogger(__name__)


class YMusicPlaybackProvider(PlaybackProvider):

    def translate_uri(self, uri):
        logger.info(f'Translate URI: {uri}')

        _, ref_type, params = uri.split(':', 2)
        if ref_type != 'track':
            return

        track_id, *_ = params.split(':', 1)
        infos = self.backend.client.tracks_download_info(track_id, get_direct_links=True)
        for info in infos:
            logger.info(f'Got info: {info}')
            if info.codec == 'mp3' and info.bitrate_in_kbps == self.backend.config['ymusic']['bitrate']:
                return info.direct_link
