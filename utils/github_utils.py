import requests
import logging
from PySide6.QtCore import QThread, Signal
import urllib3
import re

# 禁用不安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class GithubStarFetcher(QThread):
    stars_fetched = Signal(str)

    def __init__(self, repo_url, proxy=None):
        super().__init__()
        self.repo_url = repo_url
        self.proxy = proxy
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/vnd.github.v3+json"
        }

    def run(self):
        stars = self._fetch_stars()
        self.stars_fetched.emit(stars)

    def _fetch_stars(self):
        try:
            parts = self.repo_url.rstrip('/').split('/')
            if len(parts) < 2:
                return "N/A"
            
            owner = parts[-2]
            repo = parts[-1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            
            # 策略1: 尝试使用提供的代理
            if self.proxy:
                try:
                    proxies = {"http": self.proxy, "https": self.proxy}
                    return self._make_request(api_url, proxies=proxies)
                except Exception as e:
                    logger.warning(f"Proxy request failed, trying without proxy: {e}")

            # 策略2: 尝试直接连接
            try:
                return self._make_request(api_url, proxies=None)
            except Exception as e:
                logger.warning(f"Direct request failed: {e}")

            # 策略3: 尝试忽略 SSL 验证（针对某些公司网络/抓包环境）
            try:
                return self._make_request(api_url, proxies=None, verify=False)
            except Exception as e:
                logger.error(f"All fetch strategies failed: {e}")
                
            return "Err"
        except Exception as e:
            logger.error(f"Critical error in star fetcher: {e}")
            return "Err"

    def _make_request(self, url, proxies=None, verify=True):
        response = requests.get(
            url, 
            proxies=proxies, 
            timeout=8, 
            headers=self.headers, 
            verify=verify
        )
        if response.status_code == 200:
            data = response.json()
            count = data.get("stargazers_count", 0)
            if count >= 1000:
                return f"{count/1000:.1f}k" if count < 10000 else f"{count//1000}k"
            return str(count)
        elif response.status_code == 403:
            return "Limit"
        return "Err"

class GithubVersionChecker(QThread):
    """
    检查 GitHub 上的最新版本
    返回 (latest_version, download_url, release_notes)
    """
    version_checked = Signal(str, str, str)

    def __init__(self, repo_url, proxy=None):
        super().__init__()
        self.repo_url = repo_url
        self.proxy = proxy
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/vnd.github.v3+json"
        }

    def run(self):
        try:
            parts = self.repo_url.rstrip('/').split('/')
            if len(parts) < 2:
                self.version_checked.emit("", "", "")
                return
            
            owner = parts[-2]
            repo = parts[-1]
            # 获取最新 release
            api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            
            proxies = None
            if self.proxy:
                proxies = {"http": self.proxy, "https": self.proxy}

            # 尝试获取
            data = self._fetch_data(api_url, proxies)
            if data:
                tag_name = data.get("tag_name", "")
                # 提取版本号 (如 v0.98 -> 0.98)
                version = re.sub(r'[^0-9.]', '', tag_name)
                download_url = data.get("html_url", self.repo_url)
                body = data.get("body", "无更新说明")
                self.version_checked.emit(version, download_url, body)
            else:
                self.version_checked.emit("", "", "")
        except Exception as e:
            logger.error(f"Version check failed: {e}")
            self.version_checked.emit("", "", "")

    def _fetch_data(self, url, proxies=None):
        try:
            # 策略1: 正常请求
            response = requests.get(url, proxies=proxies, timeout=10, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            
            # 策略2: 忽略 SSL
            response = requests.get(url, proxies=proxies, timeout=10, headers=self.headers, verify=False)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
