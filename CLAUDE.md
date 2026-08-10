# CLAUDE.md

このファイルは Claude Code がこのリポジトリで作業する際のガイドです。

## プロジェクト概要

日本語ニュースサイトの RSS を定期的に巡回し、未投稿の記事を Truth Social に自動投稿する Bot。
メディアごとに別々の Truth Social アカウントへ投稿する（NHK / 朝日・産経 / BBC / CNN / 日経）。

本番環境は **Rocky Linux の VPS** 上で Docker Compose により常駐稼働している。
コードは Python 3.13 / Poetry 管理。テストコードは現状なし。

## 実行コマンド

### ローカル開発

```bash
poetry install
poetry run python -u main.py     # DATABASE_PATH の設定が必要（デフォルトは /app/db/newsbot.db）
poetry run black .               # フォーマッタ（設定変更なしのデフォルト）
poetry run pylint <target>
```

### 本番（VPS 上）

```bash
docker compose up -d --build
docker logs truth-bot --tail=100
```

`main.py` は docker-compose の `command:` で起動する（= コンテナの PID 1）。
これにより `restart: always` がボットのクラッシュ時と VPS 再起動時の両方で効く。

### メンテナンススクリプト

```bash
docker exec -d truth-bot poetry run python -u initialize.py  # 各RSSの現時点の記事を「投稿済み」として登録（初回導入・投稿爆発の防止）
docker exec -d truth-bot poetry run python -u clean.py       # 7日より古い published_urls を削除（通常は systemd timer で自動実行）
docker exec -d truth-bot poetry run python -u migration.py   # data_files/*.txt からのURL移行（レガシー・通常不要）
```

### 定期実行（VPS の systemd timer）

VPS 側では以下の独自 timer を有効にして運用している。

| timer | スケジュール | 内容 |
| --- | --- | --- |
| `truth-clean.timer` | 毎日 03:00 JST | `truth-clean.service` → `/usr/local/bin/run_clean.sh` が `clean.py` を実行（古い published_urls の削除） |
| `restart-truth-bot.timer` | 毎週月曜 05:00 JST | `restart-truth-bot.service` → `/usr/local/bin/restart_truth_bot.sh` が `docker compose stop && up -d` |

そのため `clean.py` を手動で叩く必要は通常ない。
他に動いているのは OS 標準の `dnf-makecache` / `logrotate` / `systemd-tmpfiles-clean` のみ。

**ユニットとスクリプトの実体は `systemd/` にあり、リポジトリを正とする。**
VPS 上の `/etc/systemd/system` と `/usr/local/bin` は、そこからコピーして配置する。

```bash
# VPS 上
git pull
sudo ./systemd/install.sh check     # 配置済みとリポジトリの差分を確認
sudo ./systemd/install.sh install   # コピー + restorecon + daemon-reload + enable --now
```

`/etc/systemd/system` へシンボリックリンクを張らないこと。リポジトリはホームディレクトリ配下
（`/home/rocky/truth-news-bot`）にあるため SELinux ラベルが `user_home_t` になり、systemd が
ユニットを読めなくなる。緊急対応で VPS 上を直接編集した場合は、`install.sh check` が差分を検出するので
必ずリポジトリ側に取り込んで戻すこと。

なお `restart_truth_bot.sh` は `cd /home/rocky/truth-news-bot` をハードコードしている。
デプロイ先を変える場合はここも直す。

## アーキテクチャ

### 実行フロー

`main.py` が 2 つの daemon スレッドを起動し、`queue.Queue` で繋ぐ生産者・消費者構成。

- **rss_checker スレッド** — 300 秒ごとに `news_bot.check_update()` を呼び、
  未投稿記事を `(article, retry_count)` としてキューに投入。
- **sns_publisher スレッド** — キューから 1 件取り出して `news_bot.publish()`、
  **投稿間隔は 11 秒スリープ**（Truth Social のレート制限回避のため。安易に縮めない）。
  失敗時は retry_count を増やして再エンキューし、`MAX_RETRY`（env、既定 10）超過でログに error を残して破棄。

### レイヤ構成

```
main.py          スレッド起動・キュー・リトライ制御
news_bot.py      メディア定義（RSS URL / 認証情報 / ハッシュタグ）と投稿本文の組み立て
service/
  news_feeder.py feedparser で RSS → List[Article]
  truth_social.py truthbrush.Api のラッパ（compose_truth）
  url_manager.py  SQLite による投稿済みURL管理（スレッドセーフ）
models/
  article.py     Article dataclass (title, link, media)
  media.py       Media Enum
utils/
  logger_config.py JST 対応 logger
truthbrush/      stanfordio/truthbrush をベンダリングした Truth Social API クライアント
```

### 重複投稿の防止

`service/url_manager.py` の `URLManager` が SQLite (`published_urls` テーブル、`UNIQUE(url, title)`) で管理。
`threading.Lock` + 都度 connect/close で複数スレッドから安全に使う。
重複チェックは **2 箇所**で行う（RSS 取得直後のフィルタと、投稿直前の `_post_and_save` 内）。
キュー滞留中に別経路で投稿されるケースを防ぐためなので、後者を「冗長」として消さないこと。

### メディア追加時に触る場所

`news_bot.py` に集約されている。新しいメディアを足す場合:

1. `models/media.py` の `Media` Enum に追加
2. `news_bot.py` に RSS URL 定数と `<NAME>_TRUTHSOCIAL_{USERNAME,PASSWORD,TOKEN}` の読み込みを追加
3. `check_update()` に `_process_articles(...)` の呼び出しを追加（`max_articles` で 1 巡あたりの投稿数を絞る）
4. `publish()` の `match article.media` に case を追加（ハッシュタグは `#<media>_news #inkei_news` の形式）
5. `initialize.py` の RSS URL 一覧にも追加

### 記事の選び方

`_process_articles()` は未投稿記事から **`random.sample` でランダムに `max_articles` 件**選ぶ（新着順ではない）。
これは投稿の偏りを避けるための意図的な挙動。

朝日・産経は `【` または `＞`(`＜`) で始まるタイトルを投稿せず、投稿済みURLとしてだけ登録してスキップする
（連載・特集ものを除外するため）。

## 認証情報の扱い

- 認証情報は `production.env`（gitignore 対象、`*.env`）に置き、docker-compose の `env_file` で注入する。
  **このファイルの中身をコミットしたりログに出したりしないこと。**
- `<MEDIA>_TRUTHSOCIAL_TOKEN` があればそれを使い、無ければ username/password で OAuth ログインしてトークンを取得する
  （`truthbrush/api.py` の `__check_login`）。トークンは永続化されないので、失効時は env を更新する。

## 注意点

- **DB は `./db/newsbot.db`（ホスト側にボリュームマウント）**。コンテナ削除では消えないが、
  この DB を消すと全記事が未投稿扱いになり大量投稿が発生する。消した場合は必ず `initialize.py` を先に実行する。
- `truthbrush/` は外部リポジトリのベンダリングコード。上流の変更を取り込む場合は
  `compose_truth` と `_post` のヘッダ周り（Truth Social 側の変更に追随して手を入れている）を上書きしないよう注意。
- ログは JST 表示。ログレベルは env `LOG_LEVEL`（既定 INFO）。
  `main.py` は PID 1 なので stdout がそのまま `docker logs` に流れる。
  `docker exec` で起動した各スクリプトは stdout が拾われないため、`/proc/1/fd/1` へも書き出している
  （`utils/logger_config.py`）。この分岐は `os.getpid() != 1` で判定していて、外すと本体のログが二重に出る。
- 例外は基本的に握りつぶさず `main.py` の sns_publisher までバブルアップさせ、リトライ機構に載せる設計。
