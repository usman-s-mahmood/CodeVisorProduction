import asyncio
import os
import resource
import re
from channels.generic.websocket import AsyncWebsocketConsumer

class PythonRunnerConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process = None

    async def connect(self):
        await self.accept()

    def set_limits(self):
        """Hard limits at the Linux Kernel level."""
        # 1. No new files can be created (0 bytes limit)
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
        # 2. Max 128MB RAM
        resource.setrlimit(resource.RLIMIT_AS, (128*1024*1024, 128*1024*1024))
        # 3. Max 5 seconds of CPU time
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        # 4. No child processes (prevents fork bombs)
        resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))

    async def receive(self, text_data=None):
        if not self.process:
            # PRE-CHECK: Look for obviously malicious patterns
            forbidden_pattern = re.compile(r'\b(subprocess|pty|getattr|socket)\b|os\.|eval\(|exec\(')
            
            if forbidden_pattern.search(text_data):
                await self.send(text_data="\r\n[Security Alert]: Restricted keywords detected.\r\n")
                await self.close()
                return
            '''
            forbidden = ['os.', 'subprocess', 'pty', 'getattr', 'eval(', 'exec(', 'socket']
            if any(word in text_data for word in forbidden):
                await self.send(text_data="\r\n[Security Alert]: Restricted keywords detected.\r\n")
                await self.close()
                return
            '''
            await self.start_process(text_data)
        else:
            if self.process and self.process.stdin:
                try:
                    self.process.stdin.write(text_data.encode())
                    await self.process.stdin.drain()
                except: pass

    async def start_process(self, code):
        # The internal Jailor (Prefix)
        jail_prefix = (
            "import sys\n"
            "sys.modules['os'] = None\n"
            "sys.modules['subprocess'] = None\n"
            "del __builtins__.open\n"
            "del sys\n"
        )
        
        full_script = jail_prefix + code

        try:
            self.process = await asyncio.create_subprocess_exec(
                "python3", "-u", "-c", full_script,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                preexec_fn=self.set_limits, # THE KERNEL LOCK
                env={} # THE ENVIRONMENT LOCK (Wipes all secret keys)
            )
            asyncio.create_task(self.handle_output())
        except Exception as e:
            await self.send(text_data=f"\r\n[System Error]: {str(e)}\r\n")
            await self.close()

    async def handle_output(self):
        while self.process:
            try:
                line = await self.process.stdout.read(1024)
                if not line: break
                await self.send(text_data=line.decode('utf-8', errors='replace'))
            except: break
        await self.send(text_data="\r\n[Execution Finished]\r\n")
        await self.close()

    async def disconnect(self, close_code):
        if self.process:
            try: self.process.terminate()
            except: pass