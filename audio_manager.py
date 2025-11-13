# coding:utf-8
import os
import requests
from urllib.parse import urlparse
import hashlib


class AudioManager:
    def __init__(self, audio_dir: str = "audio"):
        self.audio_dir = audio_dir
        # 确保音频目录存在
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
            
    def download_audio(self, audio_url: str) -> str:
        """
        下载音频文件并返回保存的文件名
        :param audio_url: 音频URL
        :return: 保存的文件名
        """
        if not audio_url:
            return ""
            
        try:
            # 发送请求获取音频数据
            response = requests.get(audio_url)
            response.raise_for_status()
            
            # 生成文件名（使用URL的hash值）
            url_hash = hashlib.md5(audio_url.encode()).hexdigest()
            file_extension = self._get_file_extension(audio_url)
            filename = f"{url_hash}{file_extension}"
            
            # 保存音频文件
            file_path = os.path.join(self.audio_dir, filename)
            with open(file_path, "wb") as f:
                f.write(response.content)
                
            return filename
        except Exception as e:
            print(f"下载音频失败: {e}")
            return ""
            
    def _get_file_extension(self, url: str) -> str:
        """从URL获取文件扩展名"""
        parsed_url = urlparse(url)
        path = parsed_url.path
        if "." in path:
            return path.split(".")[-1]
        return ".mp3"  # 默认扩展名