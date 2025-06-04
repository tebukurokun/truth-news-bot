from service.url_manager import URLManager

# URLManager初期化
url_manager = URLManager()


def migration():

    url_manager.migration()


if __name__ == "__main__":
    migration()
