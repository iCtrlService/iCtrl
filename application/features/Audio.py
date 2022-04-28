#  Copyright (c) 2022 iCtrl Developers
# 
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to
#   deal in the Software without restriction, including without limitation the
#   rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#   sell copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
# 
#  The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
# 
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
#   IN THE SOFTWARE.

import os
import threading
import time
import uuid
from typing import Optional

import paramiko
from SimpleWebSocketServer import SimpleSSLWebSocketServer, WebSocket, SimpleWebSocketServer

from .Connection import Connection
from .. import app
from ..utils import find_free_port

AUDIO_CONNECTIONS = {}


class Audio(Connection):
    def __init__(self):
        self.id = None
        self.transport: Optional[paramiko.Transport] = None
        self.remote_port = 0

        super().__init__()

    def __del__(self):
        print('Audio::__del__')
        if self.remote_port != 0:
            self.transport.cancel_port_forward('127.0.0.1', self.remote_port)
        if self.transport is not None:
            self.transport.close()

        super().__del__()

    def connect(self, *args, **kwargs):
        return super().connect(*args, **kwargs)

    def launch_audio(self):
        try:
            self.transport = self.client.get_transport()
            self.remote_port = self.transport.request_port_forward('127.0.0.1', 0)
        except Exception as e:
            return False, str(e)

        self.id = uuid.uuid4().hex
        AUDIO_CONNECTIONS[self.id] = self

        return True, self.id


class AudioWebSocket(WebSocket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio: Optional[Audio] = None
        self.module_id = None

    def handleConnected(self):
        audio_id = self.request.path[1:]
        if audio_id not in AUDIO_CONNECTIONS:
            print(f'AudioWebSocket: Requested audio_id={audio_id} does not exist.')
            self.close()
            return

        self.audio = AUDIO_CONNECTIONS[audio_id]

        sink_name = 'remote_' + audio_id

        # unload 5 times to clean up any previously loaded instances
        # let's hope 5 is enough
        # TODO: verify whether this would unload others' sessions
        load_module_command_list = [f'pactl unload-module module-null-sink'] * 5 \
                                   + [f'pactl load-module module-null-sink sink_name={sink_name}']
        exit_status, _, stdout, _ = self.audio.exec_command_blocking(';'.join(load_module_command_list))
        if exit_status != 0:
            print(f'AudioWebSocket: audio_id={audio_id}: unable to load pactl module-null-sink')
            return
        load_module_stdout_lines = stdout.readlines()
        self.module_id = int(load_module_stdout_lines[0])

        def writeall():
            channel = self.audio.transport.accept(10)  # FIXME: should we try again?
            if channel is None:
                raise ConnectionError(
                    f'AudioWebSocket: audio_id={audio_id}: unable to create socket on the remote target')

            while True:
                data = channel.recv(10240)
                if not data:
                    self.close()
                    break
                self.sendMessage(data)

        writer = threading.Thread(target=writeall)
        writer.start()

        time.sleep(1)  # accept() has to run before the following, let's just hope 1s is enough
        # TODO: support requesting audio format from the client
        launch_ffmpeg_command = f'killall ffmpeg; ffmpeg -f pulse -i "{sink_name}.monitor" ' \
                                f'-ac 2 -acodec pcm_s16le -ar 44100 -f s16le "tcp://127.0.0.1:{self.audio.remote_port}"'
        self.audio.client.exec_command(launch_ffmpeg_command)

    def handleClose(self):
        if self.module_id is not None:
            # unload the module before leaving
            self.audio.client.exec_command(f'pactl unload-module {self.module_id}')

        del AUDIO_CONNECTIONS[self.audio.id]
        del self.audio


# if the Flask 'app' is in debug mode, all code will be re-run (which means they will run twice) after app.run()
# since the ws server will bind to the port, we should only run it once
# if we are in debug mode, run the server in the second round
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    AUDIO_PORT = find_free_port()
    if os.environ.get('SSL_CERT_PATH') is None:
        # no certificate provided, run in non-encrypted mode
        # FIXME: consider using a self-signing certificate for local connections
        audio_server = SimpleWebSocketServer('', AUDIO_PORT, AudioWebSocket)
    else:
        import ssl

        audio_server = SimpleSSLWebSocketServer('', AUDIO_PORT, AudioWebSocket,
                                                certfile=os.environ.get('SSL_CERT_PATH'),
                                                keyfile=os.environ.get('SSL_KEY_PATH'),
                                                version=ssl.PROTOCOL_TLS)

    threading.Thread(target=audio_server.serveforever).start()