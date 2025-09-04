import asyncio
from contextlib import asynccontextmanager
import re
import os, pty, tty, termios, fcntl, select, errno, struct, signal, time

import ansi2txt



script = [
    "ls",
    "pwd",
    "echo hello",
    "exit",
]

def open_raw_pty(rows=100, cols=200):
    m, s = os.openpty()
    
    # Set the terminal size first
    fcntl.ioctl(s, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
    
    return m, s

def set_raw_mode(fd):
    """Force terminal into completely raw mode"""
    attrs = termios.tcgetattr(fd)
    
    # Input flags: disable all input processing
    attrs[0] = 0  # Clear all input flags
    
    # Output flags: disable all output processing  
    attrs[1] = 0  # Clear all output flags
    
    # Control flags: 8-bit characters
    attrs[2] = termios.CS8
    
    # Local flags: disable all local processing (echo, canonical mode, signals, etc.)
    attrs[3] = 0  # Clear all local flags
    
    # Control characters for raw mode
    cc = attrs[6]
    cc[termios.VMIN]  = 1  # Return each byte immediately
    cc[termios.VTIME] = 0  # No timeout
    
    termios.tcsetattr(fd, termios.TCSANOW, attrs)


def blocking_drain_once(fd):
    try:
        return os.read(fd, 65536)
    except OSError as e:
        if e.errno in (errno.EIO, errno.EBADF):  # slave closed
            return b""
        raise



@asynccontextmanager
async def terminal(command, onOutput=None):
    m, s = open_raw_pty(100, 200)
    pid = os.fork()
    if pid == 0:
        # child
        os.setsid()
        fcntl.ioctl(s, termios.TIOCSCTTY, 0)
        os.dup2(s, 0); os.dup2(s, 1); os.dup2(s, 2)
        os.close(m)
        env = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor")
        os.execvpe(command[0], command, env)   # your shell/program
    else:
        # parent
        os.close(s)
        
        last_change = time.monotonic()
        output = []
        checkpoint = 0

        def onActivity(chunk):
            nonlocal last_change
            last_change = time.monotonic()
            output.append(chunk)
            if onOutput:
                onOutput(chunk)

        class Terminal:
            async def send(self, input, type_delay=0.05, after_delay=0.1):
                for c in input:
                    os.write(m, c.encode())
                    # print('>', c)
                    await asyncio.sleep(type_delay)
                        
                await asyncio.sleep(after_delay)
                os.write(m, b"\n")

                nonlocal checkpoint
                checkpoint = sum(len(chunk) for chunk in output)
                
            
            async def waitForStability(self, threshold=0.3, timeout=5.0):
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    currentSilence = time.monotonic() - last_change
                    if currentSilence >= threshold:
                        return True
                    missing = threshold - currentSilence
                    await asyncio.sleep(min(missing, 0.1))  # Async sleep with max of 0.1s
                return False
            
            async def waitForOutput(self, pattern: bytes, timeout=5.0):
                # prog = re.compile(pattern)
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    buf = b''.join(output)[checkpoint:]
                    if pattern in buf:
                        return True
                    await asyncio.sleep(0.1)  # Async sleep with max of 0.1s
                return False
            
            def output(self):
                return b''.join(output)
            
            def outputChunks(self):
                return list(output)

        # Start the reader task
        loop = asyncio.get_running_loop()
        loop.add_reader(m, lambda: onActivity(blocking_drain_once(m)))

        try:
            yield Terminal()
        finally:
            loop.remove_reader(m)
            os.close(m)
            os.kill(pid, signal.SIGTERM)
            os.waitpid(pid, 0)

