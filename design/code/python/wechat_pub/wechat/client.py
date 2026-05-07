"""微信 API 客户端：access_token + 素材上传 + 草稿箱"""
import time
import json
import hashlib
import httpx
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class WeChatConfig:
    """微信配置"""
    app_id: str = ""
    app_secret: str = ""
    # 测试号模式（不校验 IP 白名单）
    sandbox: bool = False


@dataclass
class UploadResult:
    """素材上传结果"""
    media_id: str = ""
    url: str = ""  # 仅图片素材返回 url


@dataclass
class DraftResult:
    """草稿创建结果"""
    media_id: str = ""  # 草稿的 media_id


class WeChatClient:
    """微信公众号 API 客户端
    
    支持：
    - access_token 获取与缓存
    - 素材上传（图片 thumb / 内容图）
    - 草稿箱创建
    - 草稿箱列表查询
    """

    BASE_URL = "https://api.weixin.qq.com"
    SANDBOX_URL = "https://api.weixin.qq.com/sandbox"

    def __init__(self, config: WeChatConfig | dict | None = None):
        if config is None:
            config = WeChatConfig()
        elif isinstance(config, dict):
            config = WeChatConfig(**config)

        self.app_id = config.app_id
        self.app_secret = config.app_secret
        self.sandbox = config.sandbox

        # token 缓存
        self._token = ""
        self._token_expires_at = 0

    @property
    def _base(self) -> str:
        return self.SANDBOX_URL if self.sandbox else self.BASE_URL

    def _load_config_from_file(self) -> None:
        """从配置文件或环境变量加载 app_id / app_secret"""
        # 优先级：构造参数 > 环境变量 > 配置文件
        import os

        if not self.app_id:
            self.app_id = os.environ.get("WECHAT_APP_ID", "")
        if not self.app_secret:
            self.app_secret = os.environ.get("WECHAT_APP_SECRET", "")

        if self.app_id and self.app_secret:
            return

        config_path = Path.home() / ".config" / "wechat-pub" / "config.yaml"
        if not config_path.exists():
            return
        import yaml
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        wechat = data.get("wechat", {})
        if not self.app_id:
            self.app_id = wechat.get("app_id", "")
        if not self.app_secret:
            self.app_secret = wechat.get("app_secret", "")

    def is_configured(self) -> bool:
        """检查是否已配置微信凭证"""
        if not self.app_id or not self.app_secret:
            self._load_config_from_file()
        return bool(self.app_id and self.app_secret)

    # ── access_token ──────────────────────────────────────────
    def get_access_token(self) -> str:
        """获取 access_token（带缓存，提前 200s 过期）"""
        if self._token and time.time() < self._token_expires_at:
            return self._token

        if not self.is_configured():
            raise RuntimeError(
                "微信凭证未配置。请运行 wechat-pub config init "
                "或设置 WECHAT_APP_ID / WECHAT_APP_SECRET 环境变量"
            )

        resp = httpx.get(
            f"{self._base}/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.app_secret,
            },
            timeout=10,
        )
        data = resp.json()

        if "access_token" not in data:
            errcode = data.get("errcode", -1)
            errmsg = data.get("errmsg", "unknown")
            raise RuntimeError(f"获取 access_token 失败: [{errcode}] {errmsg}")

        self._token = data["access_token"]
        self._token_expires_at = time.time() + data["expires_in"] - 200
        return self._token

    # ── 素材上传 ─────────────────────────────────────────────
    def upload_image(
        self, file_path: str, image_type: str = "thumb"
    ) -> UploadResult:
        """上传图片到微信素材库

        Args:
            file_path: 本地图片路径
            image_type: thumb (封面缩略图) 或 content (正文图片)

        Returns:
            UploadResult 包含 media_id 和可选 url
        """
        token = self.get_access_token()
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {file_path}")

        # 微信限制：图片 ≤ 5MB
        if path.stat().st_size > 5 * 1024 * 1024:
            raise ValueError(f"图片超过 5MB 限制: {file_path}")

        with open(path, "rb") as f:
            resp = httpx.post(
                f"{self._base}/cgi-bin/material/add_material",
                params={"access_token": token, "type": image_type},
                files={"media": (path.name, f, "image/jpeg")},
                timeout=30,
            )

        data = resp.json()
        if "media_id" not in data:
            errcode = data.get("errcode", -1)
            errmsg = data.get("errmsg", "unknown")
            raise RuntimeError(f"上传图片失败: [{errcode}] {errmsg}")

        return UploadResult(
            media_id=data["media_id"],
            url=data.get("url", ""),
        )

    def upload_content_image(self, file_path: str) -> str:
        """上传正文图片，返回微信图片 URL

        微信公众号正文中的图片必须用 uploadimg 接口上传，
        返回的 URL 才能在正文中使用。
        """
        token = self.get_access_token()
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {file_path}")

        with open(path, "rb") as f:
            resp = httpx.post(
                f"{self._base}/cgi-bin/media/uploadimg",
                params={"access_token": token},
                files={"media": (path.name, f, "image/jpeg")},
                timeout=30,
            )

        data = resp.json()
        if "url" not in data:
            errcode = data.get("errcode", -1)
            errmsg = data.get("errmsg", "unknown")
            raise RuntimeError(f"上传正文图片失败: [{errcode}] {errmsg}")

        return data["url"]

    # ── 草稿箱 ───────────────────────────────────────────────
    def create_draft(
        self,
        title: str,
        content: str,
        thumb_media_id: str = "",
        author: str = "",
        digest: str = "",
        show_cover_pic: int = 0,
    ) -> DraftResult:
        """创建微信公众号草稿

        Args:
            title: 文章标题（≤64字符）
            content: 正文 HTML（≤20000字符）
            thumb_media_id: 封面图片 media_id（必须已上传到素材库）
            author: 作者（≤16字符）
            digest: 摘要（≤128字符，空则自动截取正文前120字）
            show_cover_pic: 是否在正文显示封面（0=不显示）

        Returns:
            DraftResult 包含 media_id
        """
        token = self.get_access_token()

        # 校验
        if len(title) > 64:
            raise ValueError(f"标题超过 64 字符限制（当前 {len(title)} 字符）")
        if len(content) > 20000:
            raise ValueError(f"正文超过 20000 字符限制（当前 {len(content)} 字符）")

        # 自动截取摘要
        if not digest:
            # 去掉 HTML 标签取纯文本
            import re
            plain = re.sub(r"<[^>]+>", "", content)
            digest = plain[:120].strip()

        article = {
            "title": title,
            "author": author or "",
            "digest": digest or "",
            "content": content,
            "show_cover_pic": show_cover_pic,
        }

        if thumb_media_id:
            article["thumb_media_id"] = thumb_media_id

        resp = httpx.post(
            f"{self._base}/cgi-bin/draft/add",
            params={"access_token": token},
            json={"articles": [article]},
            timeout=15,
        )

        data = resp.json()
        if "media_id" not in data:
            errcode = data.get("errcode", -1)
            errmsg = data.get("errmsg", "unknown")
            raise RuntimeError(f"创建草稿失败: [{errcode}] {errmsg}")

        return DraftResult(media_id=data["media_id"])

    def list_drafts(self, offset: int = 0, count: int = 5) -> list[dict]:
        """获取草稿列表"""
        token = self.get_access_token()
        resp = httpx.post(
            f"{self._base}/cgi-bin/draft/batchget",
            params={"access_token": token},
            json={"offset": offset, "count": count, "no_content": 1},
            timeout=10,
        )
        data = resp.json()
        return data.get("item", [])

    def delete_draft(self, media_id: str) -> bool:
        """删除草稿"""
        token = self.get_access_token()
        resp = httpx.post(
            f"{self._base}/cgi-bin/draft/delete",
            params={"access_token": token},
            json={"media_id": media_id},
            timeout=10,
        )
        return resp.json().get("errcode", -1) == 0
