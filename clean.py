# URLManager初期化
from service.url_manager import URLManager

url_manager = URLManager()


def clean():

    url_manager.cleanup_old_urls(7)  # 7日以上前のURLを削除


if __name__ == "__main__":
    clean()
