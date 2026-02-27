# -*- coding: utf-8 -*-

import base64
import tempfile
import sounddevice as sd
import soundfile as sf
import time
import os
import uuid

from tencentcloud.common import credential
from tencentcloud.tts.v20190823 import tts_client, models
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException


class TencentTTS:
    def __init__(self, secret_id, secret_key):
        cred = credential.Credential(secret_id, secret_key)

        httpProfile = HttpProfile()
        httpProfile.endpoint = "tts.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile

        self.client = tts_client.TtsClient(cred, "ap-shanghai", clientProfile)

    def speak(self, text, interrupt_event=None):
        """
        text: 中文文本（只放在 Text 里，安全）
        interrupt_event: 返回 True 时中断播放
        """
        req = models.TextToVoiceRequest()
        req.Text = text
        req.SessionId = uuid.uuid4().hex  # ✅ 全 ASCII，避免 latin-1 问题
        req.VoiceType = 101016            # 情感女声
        req.Speed = 0
        req.Volume = 5
        req.SampleRate = 16000
        req.Codec = "wav"
        req.EmotionCategory = "calm"
        req.EmotionIntensity = 100

        try:
            resp = self.client.TextToVoice(req)
        except TencentCloudSDKException as e:
            print(f"[Tencent TTS 调用失败] {e}")
            return

        audio_data = base64.b64decode(resp.Audio)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.write(audio_data)
        tmp.close()

        data, fs = sf.read(tmp.name, dtype="float32")
        os.remove(tmp.name)

        sd.play(data, fs)

        # 🔥 手动轮询可打断
        while sd.get_stream().active:
            if interrupt_event and interrupt_event():
                sd.stop()
                break
            time.sleep(0.05)
