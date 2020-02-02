import aiohttp
import discord
import io
import asyncio
import os

class TTSRequestError(Exception):
    pass

class TTS:
    def __init__(self, message, file_path: str):
        self.message = message
        self.file_path = file_path

    async def work(self):
        voice = self.message.author.voice

        if voice is None or voice.channel is None:
            await self.message.channel.send("Sa pole kõnes")
            return None

        self.build_params()
        await self.fetch_tts_audio_file()
        vc = await voice.channel.connect()
        vc.play(discord.FFmpegPCMAudio(self.file_path, executable=r"C:\Software\ffmpeg\bin\ffmpeg.exe"))
        while True:
            await asyncio.sleep(1)
            if not vc.is_playing():
                break
        await vc.disconnect()
        os.remove(self.file_path)
        
    def build_params(self):
        self.params = {
            "pitch":"169",
            "speed":"170"
        }

        presets = {
            "DEMON": "Female Whisper",
            "ROBOT": "RoboSoft Two"
        }
        text = [x for x in self.message.content.split(" ")[1:] if x]

        if text[0] in presets:
            self.params["text"] = " ".join(text[1:])
            self.params["voice"] = presets[text[0]]
        else:
            self.params["text"] = " ".join(text)
            self.params["voice"] = "Mary"
    
    async def fetch_tts_audio_file(self):
        '''
        response = requests.get("https://tetyys.com/SAPI4/SAPI4", params=self.params)
        if response.status_code != 200:
            raise TTSRequestError(response.status_code)
        self.binary = "temp.wav"#io.BytesIO(response.content)
        with open(self.binary, "wb") as fptr:
            fptr.write(response.content)
        '''
        url = "https://tetyys.com/SAPI4/SAPI4?" + "&".join([f"{k}={self.params[k]}" for k in self.params])
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise TTSRequestError(resp.status)
                with open(self.file_path, "wb") as fptr:
                    fptr.write(await resp.read())
