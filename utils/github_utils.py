import requests
import logging
from PySide6.QtCore import QThread, Signal
import urllib3

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
            # 格式化数字：如果是 1590 -> 1,590
            count = data.get("stargazers_count", 0)
            if count >= 1000:
                return f"{count/1000:.1f}k" if count < 10000 else f"{count//1000}k"
            return str(count)
        elif response.status_code == 403:
            return "Limit" # API 速率限制
        return "Err"
