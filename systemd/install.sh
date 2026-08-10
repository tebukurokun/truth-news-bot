#!/bin/bash
#
# VPS 上の systemd ユニットと補助スクリプトを、このリポジトリの内容に合わせる。
#
#   sudo ./systemd/install.sh check     # 配置済みのものとリポジトリの差分を表示するだけ
#   sudo ./systemd/install.sh install   # 配置 + daemon-reload + timer の enable
#
# リポジトリを正とし、/etc へはコピーする（シンボリックリンクにしない）。
# ホームディレクトリ配下のファイルは SELinux ラベルが user_home_t になり、
# systemd がユニットを読めなくなるため。
#
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DEST=/etc/systemd/system
BIN_DEST=/usr/local/bin

UNITS=(
  truth-clean.timer
  truth-clean.service
  restart-truth-bot.timer
  restart-truth-bot.service
)
SCRIPTS=(
  run_clean.sh
  restart_truth_bot.sh
)
TIMERS=(
  truth-clean.timer
  restart-truth-bot.timer
)

require_root() {
  if [[ $EUID -ne 0 ]]; then
    echo "root で実行してください（sudo $0 $*）" >&2
    exit 1
  fi
}

do_check() {
  local rc=0
  for unit in "${UNITS[@]}"; do
    diff -u "$UNIT_DEST/$unit" "$SRC_DIR/$unit" || rc=1
  done
  for script in "${SCRIPTS[@]}"; do
    diff -u "$BIN_DEST/$script" "$SRC_DIR/bin/$script" || rc=1
  done

  if [[ $rc -eq 0 ]]; then
    echo "OK: 配置済みの内容はリポジトリと一致しています"
  else
    echo "" >&2
    echo "差分あり: VPS 上で直接編集された可能性があります。" >&2
    echo "リポジトリ側が正しいなら install、VPS 側が正しいならリポジトリに取り込んでください。" >&2
  fi
  return $rc
}

do_install() {
  require_root install

  for unit in "${UNITS[@]}"; do
    install -m 644 "$SRC_DIR/$unit" "$UNIT_DEST/$unit"
  done
  for script in "${SCRIPTS[@]}"; do
    install -m 755 "$SRC_DIR/bin/$script" "$BIN_DEST/$script"
  done

  # SELinux 有効環境では配置後にラベルを付け直す
  if command -v restorecon >/dev/null 2>&1; then
    for unit in "${UNITS[@]}"; do
      restorecon -F "$UNIT_DEST/$unit"
    done
    for script in "${SCRIPTS[@]}"; do
      restorecon -F "$BIN_DEST/$script"
    done
  fi

  systemctl daemon-reload
  systemctl enable --now "${TIMERS[@]}"

  echo ""
  systemctl list-timers "${TIMERS[@]}" --all
}

case "${1:-install}" in
  check)   do_check ;;
  install) do_install ;;
  *)
    echo "usage: $0 [install|check]" >&2
    exit 1
    ;;
esac
