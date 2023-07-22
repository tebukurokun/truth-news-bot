from nhk_news_feed import get_updated_articles, Article
from truth_social import compose_truth


def publish():
    updated_articles = get_updated_articles()

    if not updated_articles:
        print("no article")

    for article in updated_articles:
        print(article.title)
        content = f'{article.title}\n{article.link}'
        compose_truth(content)


if __name__ == '__main__':
    publish()
