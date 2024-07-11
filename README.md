# XTreamCode Server
This library allow to expose medias over XTreamCode API

It can be used to create application on top of XTreamCode API

Typically, create a media server that can be read by any player on your SmartTV

## Application compatible
All application compatible with XTreamCode protocol can work with this library.
It has been tested with SetIPTV (Samsung TV) and IPTV Smarters (Android).

## Quick start
You can test it by streaming your local media with below line

`python -m xtreamcodeserver -vod /my/media/path -serie /my/media/serie`

This command line will expose on your network your medias: mkv, avi, mp4.

Default credentials: username=test&password=test
Default port: 8081

For more option refer you to help

`python -m xtreamcodeserver -help`

## How to access my media
Below are some usefull URLs
    ### Server/User informations
    http://127.0.0.1:8081/player_api.php?username=test&password=test

    ### Download playlist.m3u
    http://127.0.0.1:8081/get.php?username=test&password=test&type=m3u_plus&output=ts

    ### Get JSON information
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
	
    ### Stream live content
	http://127.0.0.1:8081/live/test/test/1594066936.m3u8
	http://127.0.0.1:8081/live/test/test/1594066936.ts

    ### Stream vod content
    http://127.0.0.1:8081/movie/test/test/7511585546.mkv

## Not supported
 - tmdb cannot be provided
 - video and audio information cannot be provided
 - cover_big and movie_image are same

## Additional link/features supported by this server (And not officially supported by XTreamCode)
 - username= password= can be replace by u= p= (Kind of shortcut)
 - m3u playlist can be filter:
  http://127.0.0.1:8081/get.php?u=test&p=test&filter=serie
  http://127.0.0.1:8081/get.php?u=test&p=test&filter=vod
  http://127.0.0.1:8081/get.php?u=test&p=test&filter=live
  http://127.0.0.1:8081/get.php?u=test&p=test&category_id=1111
  
## Documentation
https://xtream-ui.org/api-xtreamui-xtreamcode/
