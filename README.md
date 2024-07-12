# XTreamCode Server
XTreamCodeServer is a simple API to expose media over XTreamCode API

```
from xtreamcodeserver import *

#Create credentials test/test
credentials_provider = XTreamCodeCredentialsMemoryProvider()
credentials_provider.add_or_update_credentials(XTreamCodeCredentials("test", "test"))

#Add MyMovie.mkv to CategoryName
entry_provider = XTreamCodeEntryMemoryProvider()
category1 = XTreamCodeCategory(name="CategoryName", category_type=XTreamCodeType.VOD)
category1.add_entry(XTreamCodeVod(name="MyMovie", extension=".mkv", stream=XTreamCodeFileSystemStream("./MyMovie.mkv"), description="This is the description for MyMovie"))
entry_provider.add_category(category1)

#Start server
server_xtreamcode = XTreamCodeServer(entry_provider, None, credentials_provider)
server_xtreamcode.setup("0.0.0.0", 8081, "http://127.0.0.1")
server_xtreamcode.start()

print("Server started, it will stop automatically after 10s...")

time.sleep(10)
server_xtreamcode.stop()
```

## Compatibility
This library has been tested with various applications (Box, TV, FireStick, ....)

## Quick start
You can test it by streaming your local media with below line

`python -m xtreamcodeserver -vod /my/media/path -serie /my/media/serie`

This command line will search for "mkv, avi, mp4" movies and expose them on your network.

- Credentials: username=test&password=test
- Port: 8081

For more option refer you to the help

`python -m xtreamcodeserver -h`

## How to access my media

Below are some usefull URLs

### Server/User informations
```
http://127.0.0.1:8081/player_api.php?username=test&password=test
```
### Download playlist.m3u
```
http://127.0.0.1:8081/get.php?username=test&password=test&type=m3u_plus&output=ts
```

### Get JSON information
```
http://127.0.0.1:8081/player_api.php?username=test&password=test&action=get_live_categories
http://127.0.0.1:8081/player_api.php?username=test&password=test&action=get_vod_categories
http://127.0.0.1:8081/player_api.php?username=test&password=test&action=get_series_categories
http://127.0.0.1:8081/player_api.php?username=test&password=test&action=get_live_streams
http://127.0.0.1:8081/player_api.php?username=test&password=test&action=get_vod_streams
http://127.0.0.1:8081/player_api.php?username=test&password=test&action=get_series
http://127.0.0.1:8081/player_api.php?username=test&password=test&action=get_series_info
http://127.0.0.1:8081/player_api.php?username=test&password=test&action=get_vod_info
http://127.0.0.1:8081/player_api.php?username=test&password=test&action=get_short_epg&stream_id=1984029872
http://127.0.0.1:8081/player_api.php?username=test&password=test&action=get_simple_data_table
```
	
### Stream live content
```
http://127.0.0.1:8081/live/test/test/1594066936.m3u8
http://127.0.0.1:8081/live/test/test/1594066936.ts
```
Where 1594066936 is the ID of the media to stream

### Stream vod content
```
http://127.0.0.1:8081/movie/test/test/7511585546.mkv
```

## Not supported
 - tmdb cannot be provided
 - video and audio information cannot be provided
 - cover_big and movie_image are same

## Additional link/features supported by this server (And not officially supported by XTreamCode)
 - username= password= can be replace by u= p= (Kind of shortcut)
 - m3u playlist can be filter:
```
http://127.0.0.1:8081/get.php?u=test&p=test&filter=serie
http://127.0.0.1:8081/get.php?u=test&p=test&filter=vod
http://127.0.0.1:8081/get.php?u=test&p=test&filter=live
http://127.0.0.1:8081/get.php?u=test&p=test&category_id=1111
```

## Documentation
https://xtream-ui.org/api-xtreamui-xtreamcode/
