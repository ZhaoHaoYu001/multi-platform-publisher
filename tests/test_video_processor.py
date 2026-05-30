"""视频处理器测试模块."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.media.video_processor import FFmpegNotFoundError, VideoInfo, VideoProcessor


@pytest.fixture
def processor():
    """创建视频处理器实例."""
    return VideoProcessor()


@pytest.fixture
def temp_dir():
    """创建临时目录."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestVideoInfo:
    """视频信息测试."""

    def test_str(self):
        """测试字符串表示."""
        info = VideoInfo(
            duration=125.5,
            width=1920,
            height=1080,
            fps=30.0,
            size=50 * 1024 * 1024,  # 50MB
            format="mp4",
            bitrate=5000000,
        )
        result = str(info)
        assert "1920x1080" in result
        assert "30.0fps" in result
        assert "2:05" in result  # 125秒 = 2分5秒
        assert "50.00MB" in result
        assert "mp4" in result


class TestVideoProcessorInit:
    """视频处理器初始化测试."""

    def test_default_init(self):
        """测试默认初始化."""
        processor = VideoProcessor()
        assert processor._ffmpeg_path == "ffmpeg"
        assert processor._ffprobe_path == "ffprobe"

    def test_custom_ffmpeg_path(self):
        """测试自定义ffmpeg路径."""
        processor = VideoProcessor(ffmpeg_path="/usr/local/bin/ffmpeg")
        assert processor._ffmpeg_path == "/usr/local/bin/ffmpeg"
        assert processor._ffprobe_path == "/usr/local/bin/ffprobe"


class TestFFmpegCheck:
    """ffmpeg检查测试."""

    def test_check_ffmpeg_installed(self, processor):
        """测试检查已安装的ffmpeg."""
        # 根据实际环境判断
        result = processor.check_ffmpeg()
        # 不强制要求，因为测试环境可能没有ffmpeg
        assert isinstance(result, bool)

    def test_check_ffmpeg_not_found(self):
        """测试ffmpeg不存在的情况."""
        processor = VideoProcessor(ffmpeg_path="/nonexistent/ffmpeg")
        assert processor.check_ffmpeg() is False

    def test_get_ffmpeg_version(self, processor):
        """测试获取ffmpeg版本."""
        version = processor.get_ffmpeg_version()
        if processor.check_ffmpeg():
            assert version is not None
            assert "." in version
        else:
            assert version is None


class TestVideoInfoExtraction:
    """视频信息提取测试."""

    def test_get_video_info_not_found(self, processor):
        """测试文件不存在."""
        with pytest.raises(FileNotFoundError):
            processor.get_video_info("nonexistent.mp4")

    @patch("subprocess.run")
    def test_get_video_info_no_ffmpeg(self, mock_run, processor):
        """测试ffmpeg未安装."""
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(FFmpegNotFoundError):
            processor.get_video_info("test.mp4")

    @patch("subprocess.run")
    def test_get_video_info_success(self, mock_run, processor):
        """测试成功获取视频信息."""
        # 模拟ffprobe输出
        mock_output = """{
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1"
                }
            ],
            "format": {
                "duration": "120.5",
                "size": "10485760",
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                "bit_rate": "5000000"
            }
        }"""

        mock_run.side_effect = [
            MagicMock(returncode=0),  # check_ffmpeg
            MagicMock(returncode=0, stdout=mock_output),  # ffprobe
        ]

        info = processor.get_video_info("test.mp4")
        assert info.width == 1920
        assert info.height == 1080
        assert info.fps == 30.0
        assert info.duration == 120.5

    def test_is_valid_video_not_exists(self, processor):
        """测试无效视频文件."""
        assert processor.is_valid_video("nonexistent.mp4") is False


class TestVideoCompression:
    """视频压缩测试."""

    @patch("subprocess.run")
    def test_compress_no_ffmpeg(self, mock_run, processor):
        """测试ffmpeg未安装时压缩."""
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(FFmpegNotFoundError):
            processor.compress_video("input.mp4", "output.mp4")

    @patch("subprocess.run")
    def test_compress_success(self, mock_run, processor):
        """测试成功压缩视频."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # check_ffmpeg
            MagicMock(returncode=0),  # compress
        ]

        result = processor.compress_video(
            "input.mp4",
            "output.mp4",
            quality=28,
        )
        assert result == "output.mp4"

    @patch("subprocess.run")
    def test_compress_with_target_size(self, mock_run, processor):
        """测试指定目标大小压缩."""
        # 模拟get_video_info的返回
        mock_output = """{
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080, "r_frame_rate": "30/1"}],
            "format": {"duration": "120.0", "size": "10485760", "format_name": "mp4", "bit_rate": "5000000"}
        }"""

        mock_run.side_effect = [
            MagicMock(returncode=0),  # check_ffmpeg (get_video_info)
            MagicMock(returncode=0, stdout=mock_output),  # ffprobe
            MagicMock(returncode=0),  # check_ffmpeg (compress)
            MagicMock(returncode=0),  # compress
        ]

        result = processor.compress_video(
            "input.mp4",
            "output.mp4",
            target_size_mb=50,
        )
        assert result == "output.mp4"


class TestThumbnailExtraction:
    """缩略图提取测试."""

    @patch("subprocess.run")
    def test_extract_thumbnail_no_ffmpeg(self, mock_run, processor):
        """测试ffmpeg未安装时提取缩略图."""
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(FFmpegNotFoundError):
            processor.extract_thumbnail("video.mp4", "thumb.jpg")

    @patch("subprocess.run")
    def test_extract_thumbnail_success(self, mock_run, processor):
        """测试成功提取缩略图."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # check_ffmpeg
            MagicMock(returncode=0),  # extract
        ]

        result = processor.extract_thumbnail(
            "video.mp4",
            "thumbnail.jpg",
            time=5.0,
        )
        assert result == "thumbnail.jpg"

    @patch("subprocess.run")
    def test_extract_thumbnail_at_zero(self, mock_run, processor):
        """测试在0秒处提取缩略图."""
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=0),
        ]

        result = processor.extract_thumbnail(
            "video.mp4",
            "thumb.jpg",
            time=0.0,
        )
        assert result == "thumb.jpg"
