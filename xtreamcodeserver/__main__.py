# Specifications
# https://xtream-ui.org/api-xtreamui-xtreamcode/

from xtreamcodeserver import *
from xtreamcodeserver.providers.inmemory.credentials_provider import XTreamCodeCredentialsMemoryProvider
from xtreamcodeserver.providers.inmemory.entry_provider import XTreamCodeEntryMemoryProvider
from xtreamcodeserver.entry.serie_season import XTreamCodeSeason
from xtreamcodeserver.stream.filesystemstream import *
import time
import logging
import argparse
import sys

_LOGGER = logging.getLogger(__name__)

# -------------------------------------------------------

def browse_folder(path, type):
    category_list = {}
    serie_list = {}

    _LOGGER.debug("Listing %s..." % (path))

    try:
        for root, dirs, files in os.walk(path):
            for filename in files:
                fullpath = os.path.join(root, filename)
                _LOGGER.debug("Listing %s..." % (fullpath))
                filename_wo_ext, extension = os.path.splitext(filename)
                folder_name = os.path.basename(os.path.dirname(fullpath))

                if not extension in [".mkv", ".mp4", ".avi"]:
                    _LOGGER.warning(f"Ignoring file: {fullpath} (Do not have allowed extension)")
                    pass

                if type == XTreamCodeType.VOD:
                    if not folder_name in category_list:
                        category_list[folder_name] = XTreamCodeCategory(name=folder_name, category_type=type)

                    category_list[folder_name].add_entry(XTreamCodeVod(name=filename_wo_ext, extension=extension, stream=XTreamCodeFileSystemStream(fullpath), description=f"This is the description for {filename_wo_ext}"))

                elif type == XTreamCodeType.SERIE:

                    if not "all_series" in category_list:
                        category_list["all_series"] = XTreamCodeCategory(name=folder_name, category_type=type)
                    if not folder_name in serie_list:
                        serie_list[folder_name] = XTreamCodeSerie(name=folder_name)
                        category_list["all_series"].add_entry(serie_list[folder_name])

                    season_regexp = r"(?:s|saison|season)?\s?(\d{1,2})\s?(?:e|x|episode|épisode|ep)\s?(\d{1,2})"
                    match = re.search(season_regexp, filename, re.I)
                    if match:
                        season = serie_list[folder_name].get_season(int(match.group(1)))
                        if season == None:
                            season = XTreamCodeSeason(season_number=int(match.group(1)), name=filename_wo_ext, cover_url=None, description=None)
                            serie_list[folder_name].add_season(season)

                        season.add_episode(XTreamCodeEpisode(episode_number=int(match.group(2)), name=filename_wo_ext, extension=extension, stream=XTreamCodeFileSystemStream(fullpath)))
                    else:
                        _LOGGER.warning(f"Ignoring serie: {fullpath} (Unable to determine Season/Episode)")

    except:
        _LOGGER.exception(f"Exception while browsing folder: {path}")

    return category_list

# -------------------------------------------------------

def main():
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("-vod", help="Path where vods are located", type=str)
    parser.add_argument("-serie", help="Path where series are located", type=str)
    parser.add_argument("-login", help="login used to browse xtreamcode server", default="test", type=str)
    parser.add_argument("-password", help="password used to browse xtreamcode server", default="test", type=str)
    parser.add_argument("-port", help="http port", default=8081, type=int)
    parser.add_argument("-addr", help="Address to bind", default="0.0.0.0", type=str)
    parser.add_argument("-external_url", help="External url how to expose server (http://192.168.1.xx:8081)", type=str)
    
    args = parser.parse_args()
    
    credentials_provider = XTreamCodeCredentialsMemoryProvider()
    credentials_provider.add_or_update_credentials(XTreamCodeCredentials(args.login, args.password))

    entry_provider = XTreamCodeEntryMemoryProvider()
    
    server_xtreamcode = XTreamCodeServer(entry_provider, None, credentials_provider)
    
    server_xtreamcode.setup(args.addr, args.port, args.external_url)
    
    if args.vod:
        categories_vod = browse_folder(args.vod, XTreamCodeType.VOD)
        if not categories_vod:
            _LOGGER.error(f"No vod found in {args.vod} !")
            sys.exit(1)

        for category_name, xtreamcode_category in categories_vod.items():
            entry_provider.add_category(xtreamcode_category)

    if args.serie:
        categories_serie = browse_folder(args.serie, XTreamCodeType.SERIE)
        if not categories_serie:
            _LOGGER.error(f"No serie found in {args.serie} !")
            sys.exit(1)

        for category_name, xtreamcode_category in categories_serie.items():
            entry_provider.add_category(xtreamcode_category)

    _LOGGER.info('Starting XTreamCode http server...')
    server_xtreamcode.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    server_xtreamcode.stop()
    _LOGGER.info('Stopped XTreamCode http server')
    
if __name__ == '__main__':
    main()