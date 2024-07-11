import logging
import threading
import re
from xtreamcodeserver.interfaces.stream import IXTreamCodeStream
import queue
from http import HTTPStatus

from xtreamcodeserver.utils.http_utils import HTTPUtils

_LOGGER = logging.getLogger(__name__)

#Documentation: https://kkroening.github.io/ffmpeg-python/

class XTreamCodeTranscodeStream(IXTreamCodeStream, threading.Thread):
    def __init__(self, stream, type="webm"):
        threading.Thread.__init__(self)
        self.stream = stream
        self.m_type = type
        self.m_buffer = queue.Queue()
        self.m_ffmpeg_stream = None
        self.m_ffmpeg_process = None
        self.m_start_offset = None

    def get_uri(self) -> str:
        return self.stream.get_uri()
    
    def set_uri(self, uri: str) -> None:
        self.stream.set_uri(uri)

    def run(self):
        while self.is_running():
            ret = self.m_ffmpeg_process.stdout.readline()
            if ret:
                self.m_buffer.put(ret)

        _LOGGER.info("Stream trancoding: stopped !")

    def is_running(self):
        return (self.m_ffmpeg_process != None) and (self.m_ffmpeg_process.poll() == None)  # None means process running

    def open(self, http_req_path, http_req_headers):
        import ffmpeg

        _LOGGER.info("Stream trancoding: Opening (%s)..." %(self.m_type))

        self.m_start_offset = HTTPUtils.get_start_offset(http_req_headers)

        if not self.stream.open(http_req_path, http_req_headers):
            return False

        try:
            self.m_ffmpeg_stream = ffmpeg.input('pipe:')
            if self.m_type == "webm":
                # https://developers.google.com/media/vp9/live-encoding
                # self.m_ffmpeg_stream = ffmpeg.output(self.m_ffmpeg_stream, 'pipe:', f=self.m_type, **{'c:v': 'libvpx-vp9'}, **{'r': '30'}, **{'g': '90'}, **{'quality': 'realtime'}, **{'row-mt': '1'}, **{'qmin': '4'}, **{'qmax': '48'}, **{'s': '854x480'}, **{'speed': '6'}, **{'threads': '4'}, **{'tile-columns': '1'}, **{'frame-parallel': '1'}, **{'b:v': '1800k'} )
                self.m_ffmpeg_stream = ffmpeg.output(self.m_ffmpeg_stream, 'pipe:', f=self.m_type, **{'c:v': 'libvpx-vp9'},
                                              **{'r': '30'}, **{'g': '90'}, **{'quality': 'realtime'},
                                              **{'row-mt': '1'}, **{'qmin': '4'}, **{'qmax': '48'}, **{'s': '640x360'},
                                              **{'speed': '7'}, **{'threads': '4'}, **{'tile-columns': '1'},
                                              **{'frame-parallel': '0'}, **{'b:v': '730k'})
            elif self.m_type == "ogv":
                self.m_ffmpeg_stream = ffmpeg.output(self.m_ffmpeg_stream, 'pipe:', f=self.m_type, **{'c:v': 'libtheora'}, crf=63,
                                              **{'c:a': 'libvorbis'})  # , **{'qscale:v': '3'}, **{'qscale:a': '3'}

            self.m_ffmpeg_process = ffmpeg.run_async(self.m_ffmpeg_stream, cmd='ffmpeg', pipe_stdin=True, pipe_stdout=True,
                                                     pipe_stderr=False, quiet=False, overwrite_output=False)
        except:
            _LOGGER.exception("FFMPEG exception (Do you have ffmpeg executable in your PATH ?)")
            self.stream.close()
            return False

        threading.Thread.start(self)
        return True

    def close(self):
        if self.is_running():
            _LOGGER.info("Stream trancoding: Stopping ...")
            self.m_ffmpeg_process.terminate()
            self.join()

        self.stream.close()

        self.m_ffmpeg_stream = None
        self.m_ffmpeg_process = None
        self.m_buffer.clear()
        
    def is_opened(self):
        return self.is_running()

    def is_end_of_stream(self):
        return False #TODO

    def read_chunk(self, chunk_size=8192):
        if not self.is_running():
            _LOGGER.error("Unable to read chunk, transcoding thread not running ...")
            return None

        buffer = None

        input = self.stream.read_chunk(chunk_size)

        if self.is_running():
            if input != None:
                self.m_ffmpeg_process.stdin.write(input)

            buffer = self.m_buffer.get()

        return buffer

    def get_http_headers(self):
        http_headers = {}

        #http_headers["content-length"] = total_size - self.m_offset
        #http_headers["content-range"] = "bytes %d-%d/%d" % (self.m_offset, total_size - 1, total_size)
        return http_headers

    def get_http_status_code(self):
        if not self.is_running():
            return HTTPStatus.NOT_ACCEPTABLE

        if self.m_start_offset is not None:
            return HTTPStatus.PARTIAL_CONTENT

        return HTTPStatus.OK