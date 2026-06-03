#!/usr/bin/env bash
# install-hooks.sh — git hooks を個人 git 環境に配置
#
# 2 つの hook を installs:
#   1. pre-commit: conflict marker 検査(2026-05-27 conflict marker leak 事故対応)
#   2. pre-push:   main 直接 push 防止(2026-06-03 direct-push-after-pr-merge 事故対応)
#
# 使い方:
#   bash scripts/install-hooks.sh

set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "❌ git リポジトリ外です"
  exit 1
}
HOOKS_DIR="$REPO_ROOT/.git/hooks"
mkdir -p "$HOOKS_DIR"

# ─── pre-commit: conflict marker 検査 ───
cat > "$HOOKS_DIR/pre-commit" <<'HOOK'
#!/usr/bin/env bash
# Auto-installed by scripts/install-hooks.sh
# 2026-05-27 conflict marker leak prevention
set -e

SCRIPT="$(git rev-parse --show-toplevel)/scripts/check-conflict-markers.sh"
if [[ -x "$SCRIPT" ]]; then
  bash "$SCRIPT" --staged
fi
HOOK
chmod +x "$HOOKS_DIR/pre-commit"
echo "✅ pre-commit hook 配置完了: $HOOKS_DIR/pre-commit"

# ─── pre-push: main 直接 push 防止 ───
cat > "$HOOKS_DIR/pre-push" <<'HOOK'
#!/usr/bin/env bash
# Auto-installed by scripts/install-hooks.sh
# 2026-06-03 direct-push-after-pr-merge prevention
#
# main / master / production ブランチへの直接 push を block。
# 緊急時バイパス: ALLOW_DIRECT_MAIN_PUSH=1 git push
# 詳細: .company/lessons-learned/2026-06-03-direct-push-after-pr-merge.md

set -e

remote="$1"
url="$2"

protected_branches="main master production"

# stdin で各 ref の情報が来る: <local_ref> <local_sha> <remote_ref> <remote_sha>
while read local_ref local_sha remote_ref remote_sha; do
  # 削除push(local_sha=0...0)はスキップ
  if [[ "$local_sha" =~ ^0+$ ]]; then continue; fi

  # remote_ref が refs/heads/{protected} なら block
  for branch in $protected_branches; do
    if [[ "$remote_ref" == "refs/heads/$branch" ]]; then
      if [[ "${ALLOW_DIRECT_MAIN_PUSH:-}" == "1" ]]; then
        echo "⚠️  ALLOW_DIRECT_MAIN_PUSH=1 で main 直接 push をバイパスします(緊急時のみ)"
      else
        cat <<EOF >&2
❌ main / master / production への直接 push は禁止です(2026-06-03 制定)

  PR merge 直後の自動 main 復帰に気付かず直接 push する事故を防ぐためのガードです。
  feature branch を切って Pull Request 化してください:

    git checkout -b feat/PRJ-\$(date +%Y%m%d)-{slug}
    git push -u origin feat/PRJ-\$(date +%Y%m%d)-{slug}
    gh pr create

  緊急時(本番障害修正等)で本ガードをバイパスする場合:

    ALLOW_DIRECT_MAIN_PUSH=1 git push

  詳細: .company/lessons-learned/2026-06-03-direct-push-after-pr-merge.md
  ルール: memory/feedback_git_deploy_policy.md / feedback_merge_on_explicit_approval.md
EOF
        exit 1
      fi
    fi
  done
done

exit 0
HOOK
chmod +x "$HOOKS_DIR/pre-push"
echo "✅ pre-push hook 配置完了: $HOOKS_DIR/pre-push"

echo ""
echo "確認:"
echo "  - git commit:  staged ファイルに conflict marker があれば block"
echo "  - git push:    main / master / production への直接 push を block"
echo ""
echo "一時バイパス:"
echo "  - pre-commit:  git commit --no-verify"
echo "  - pre-push:    ALLOW_DIRECT_MAIN_PUSH=1 git push"
echo ""
echo "(--no-verify / ALLOW_DIRECT_MAIN_PUSH を使った場合も CI 検査で検出されます)"
