"""视频处理器模块.

本模块提供了视频的获取信息、压缩和缩略图提取功能。
依赖ffmpeg进行视频处理。
"""

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class VideoInfo:
    """视频信息数据类.

    Attributes:
        duration: 视频时长（秒）
        width: 视频宽度（像素）
        height: 视频高度（像素）
        fps: 帧率
        size: 文件大小（字节）
        format: 视频格式
        bitrate: 比特率（bps）
    """

    duration: float
    width: int
    height: int
    fps: float
    size: int
    format: str
    bitrate: int

    def __str__(self) -> str:
        """返回视频信息的字符串表示."""
        size_mb = self.size / (1024 * 1024)
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return (
            f"{self.width}x{self.height} {self.fps:.1f}fps "
            f"{minutes}:{seconds:02d} {size_mb:.2f}MB {self.format}"
        )


class FFmpegNotFoundError(Exception):
    """ffmpeg未安装时抛出的异常."""

    pass


class VideoProcessor:
    """视频处理器，提供视频处理的各种功能.

    使用示例:
        processor = VideoProcessor()

        # 检查ffmpeg是否安装
        if processor.check_ffmpeg():
            info = processor.get_video_info("video.mp4")
            print(info)

        # 压缩视频
        processor.compress_video("input.mp4", "output.mp4", target_size_mb=50)

        # 提取缩略图
        processor.extract_thumbnail("video.mp4", "thumbnail.jpg", time=5.0)
    """

    def __init__(self, ffmpeg_path: Optional[str] = None) -> None:
        """初始化视频处理器.

        Args:
            ffmpeg_path: ffmpeg可执行文件路径，None则自动查找
        """
        self._ffmpeg_path = ffmpeg_path or "ffmpeg"
        self._ffprobe_path = ffmpeg_path.replace("ffmpeg", "ffprobe") if ffmpeg_path else "ffprobe"

    def check_ffmpeg(self) -> bool:
        """检查ffmpeg是否已安装.

        Returns:
            ffmpeg是否可用
        """
        try:
            result = subprocess.run(
                [self._ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_ffmpeg_version(self) -> Optional[str]:
        """获取ffmpeg版本号.

        Returns:
            版本号字符串，未安装返回None
        """
        try:
            result = subprocess.run(
                [self._ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # 解析第一行: "ffmpeg version x.x.x ..."
                first_line = result.stdout.split("\n")[0]
                parts = first_line.split()
                if len(parts) >= 3:
                    return parts[2]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    def get_video_info(self, video_path: str) -> VideoInfo:
        """获取视频信息.

        Args:
            video_path: 视频文件路径

        Returns:
            VideoInfo: 视频信息

        Raises:
            FileNotFoundError: 文件不存在时抛出
            FFmpegNotFoundError: ffmpeg未安装时抛出
            ValueError: 无法解析视频时抛出
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        if not self.check_ffmpeg():
            raise FFmpegNotFoundError(
                "ffmpeg未安装，请先安装ffmpeg: https://ffmpeg.org/download.html"
            )

        try:
            # 使用ffprobe获取视频信息
            cmd = [
                self._ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise ValueError(f"ffprobe执行失败: {result.stderr}")

            data = json.loads(result.stdout)

            # 查找视频流
            video_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break

            if video_stream is None:
                raise ValueError("未找到视频流")

            # 解析信息
            format_info = data.get("format", {})

            # 计算fps
            fps_str = video_stream.get("r_frame_rate", "30/1")
            if "/" in fps_str:
                num, den = fps_str.split("/")
                fps = float(num) / float(den) if float(den) > 0 else 30.0
            else:
                fps = float(fps_str)

            return VideoInfo(
                duration=float(format_info.get("duration", 0)),
                width=int(video_stream.get("width", 0)),
                height=int(video_stream.get("height", 0)),
                fps=fps,
                size=int(format_info.get("size", os.path.getsize(video_path))),
                format=format_info.get("format_name", "unknown"),
                bitrate=int(format_info.get("bit_rate", 0)),
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析ffprobe输出: {e}")

    def compress_video(
        self,
        input_path: str,
        output_path: str,
        target_size_mb: Optional[float] = None,
        quality: int = 23,
        max_width: Optional[int] = None,
    ) -> str:
        """压缩视频.

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            target_size_mb: 目标文件大小（MB），指定后自动计算比特率
            quality: CRF质量值（0-51，越小质量越高，默认23）
            max_width: 最大宽度，超过则等比缩放

        Returns:
            输出文件路径

        Raises:
            FFmpegNotFoundError: ffmpeg未安装时抛出
        """
        if not self.check_ffmpeg():
            raise FFmpegNotFoundError("ffmpeg未安装")

        # 构建ffmpeg命令
        cmd = [self._ffmpeg_path, "-i", input_path, "-y"]

        # 视频编码参数
        if target_size_mb:
            # 基于目标大小计算比特率
            info = self.get_video_info(input_path)
            target_bitrate = int((target_size_mb * 8 * 1024 * 1024) / info.duration)
            cmd.extend(["-b:v", f"{target_bitrate}"])
        else:
            # 使用CRF质量控制
            cmd.extend(["-crf", str(quality)])

        # 分辨率限制
        if max_width:
            cmd.extend(["-vf", f"scale={max_width}:-2"])

        # 音频保持原样或重新编码
        cmd.extend(["-c:a", "aac", "-b:a", "128k"])

        # 输出文件
        cmd.append(output_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 最长1小时
        )

        if result.returncode != 0:
            raise ValueError(f"视频压缩失败: {result.stderr}")

        return output_path

    def extract_thumbnail(
        self,
        video_path: str,
        output_path: str,
        time: float = 0.0,
    ) -> str:
        """提取视频缩略图.

        Args:
            video_path: 视频文件路径
            output_path: 输出图片路径
            time: 提取时间点（秒），0则取第一帧

        Returns:
            输出文件路径

        Raises:
            FFmpegNotFoundError: ffmpeg未安装时抛出
        """
        if not self.check_ffmpeg():
            raise FFmpegNotFoundError("ffmpeg未安装")

        cmd = [
            self._ffmpeg_path,
            "-i", video_path,
            "-ss", str(time),
            "-vframes", "1",
            "-f", "image2",
            "-y",
            output_path,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            raise ValueError(f"缩略图提取失败: {result.stderr}")

        return output_path

    def get_video_duration(self, video_path: str) -> float:
        """获取视频时长.

        Args:
            video_path: 视频文件路径

        Returns:
            时长（秒）
        """
        info = self.get_video_info(video_path)
        return info.duration

    def is_valid_video(self, video_path: str) -> bool:
        """检查视频文件是否有效.

        Args:
            video_path: 视频文件路径

        Returns:
            视频是否有效
        """
        try:
            if not os.path.exists(video_path):
                return False
            info = self.get_video_info(video_path)
            return info.duration > 0 and info.width > 0 and info.height > 0
        except Exception:
            return False
