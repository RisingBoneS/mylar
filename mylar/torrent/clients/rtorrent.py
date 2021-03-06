import os

from lib.rtorrent import RTorrent

import mylar
from mylar import logger, helpers

class TorrentClient(object):
    def __init__(self):
        self.conn = None

    def connect(self, host, username, password):
        if self.conn is not None:
            return self.conn

        if not host:
            return False

        if username and password:
            self.conn = RTorrent(
                host,
                username,
                password
            )
        else:
            self.conn = RTorrent(host)

        return self.conn

    def find_torrent(self, hash):
        return self.conn.find_torrent(hash)

    def get_torrent (self, torrent):
        torrent_files = []
        torrent_directory = os.path.normpath(torrent.directory)
        try:
            for f in torrent.get_files():
                if not os.path.normpath(f.path).startswith(torrent_directory):
                    file_path = os.path.join(torrent_directory, f.path.lstrip('/'))
                else:
                    file_path = f.path

                torrent_files.append(file_path)
            torrent_info = {
                'hash': torrent.info_hash,
                'name': torrent.name,
                'label': torrent.get_custom1() if torrent.get_custom1() else '',
                'folder': torrent_directory,
                'completed': torrent.complete,
                'files': torrent_files,
                'upload_total': torrent.get_up_total(),
                'download_total': torrent.get_down_total(),
                'ratio': torrent.get_ratio(),
                'total_filesize': torrent.get_size_bytes(),
                'time_started': torrent.get_time_started()
                }

        except Exception:
            raise

        return torrent_info if torrent_info else False

    def load_torrent(self, filepath):
        start = bool(mylar.RTORRENT_STARTONLOAD)

        logger.info('filepath to torrent file set to : ' + filepath)

        torrent = self.conn.load_torrent(filepath, verify_load=True)
        if not torrent:
            return False

        if mylar.RTORRENT_LABEL:
            torrent.set_custom(1, mylar.RTORRENT_LABEL)
            logger.info('Setting label for torrent to : ' + mylar.RTORRENT_LABEL)

        if mylar.RTORRENT_DIRECTORY:
            torrent.set_directory(mylar.RTORRENT_DIRECTORY)
            logger.info('Setting directory for torrent to : ' + mylar.RTORRENT_DIRECTORY)
      
        logger.info('Successfully loaded torrent.')

        #note that if set_directory is enabled, the torrent has to be started AFTER it's loaded or else it will give chunk errors and not seed
        if start:
            logger.info('[' + str(start) + '] Now starting torrent.')
            torrent.start()
        else:
            logger.info('[' + str(start) + '] Not starting torrent due to configuration setting.')
        return True

    def start_torrent(self, torrent):
        return torrent.start()

    def stop_torrent(self, torrent):
        return torrent.stop()

    def delete_torrent(self, torrent):
        deleted = []
        try:
            for file_item in torrent.get_files():
                file_path = os.path.join(torrent.directory, file_item.path)
                os.unlink(file_path)
                deleted.append(file_item.path)

            if torrent.is_multi_file() and torrent.directory.endswith(torrent.name):
                try:
                    for path, _, _ in os.walk(torrent.directory, topdown=False):
                        os.rmdir(path)
                        deleted.append(path)
                except:
                    pass
        except Exception:
            raise

        torrent.erase()

        return deleted
