#!/usr/bin/env bash
#
# zero2Leetcode —— 发布结果自检脚本
#
# 在服务器上运行，检查构建产物与线上页面是否符合预期。
#
# 用法：
#   bash scripts/verify-deploy.sh
#
set -uo pipefail

DOMAIN="${DOMAIN:-zero2leetcode.taoxie.vip}"
BASE="${BASE:-http://$DOMAIN}"
SITE_DIR="${SITE_DIR:-/home/ubuntu/shuati-coach/zero2Leetcode/_site}"

PASS=0
FAIL=0

check() { # check <描述> <期望非空的实际值>
    local desc="$1" actual="$2"
    if [ -n "$actual" ]; then
        printf '  \033[1;32m✓\033[0m %s\n' "$desc"
        PASS=$((PASS + 1))
    else
        printf '  \033[1;31m✗\033[0m %s\n' "$desc"
        FAIL=$((FAIL + 1))
    fi
}

echo "== 1. 构建产物 =="
for f in index.html 04_real_interviews/index.html 05_interview/index.html assets/css/docs.css; do
    [ -s "$SITE_DIR/$f" ] && check "$f" "ok" || check "$f" ""
done

echo
echo "== 2. 线上页面 ($BASE/04_real_interviews/index.html) =="
TMP="$(mktemp)"
CODE="$(curl -s -o "$TMP" -w '%{http_code}' "$BASE/04_real_interviews/index.html")"
echo "  HTTP $CODE, $(wc -c <"$TMP") bytes"

check "返回 200" "$([ "$CODE" = "200" ] && echo ok)"
check "使用 docs 布局 (site-shell/doc-header)" "$(grep -o 'site-shell' "$TMP" | head -1)"
check "渲染了题库标题" "$(grep -o '2026 大厂笔试机试真题题解汇总' "$TMP" | head -1)"
check "包含公司分组（阿里）" "$(grep -o '阿里巴巴笔试真题' "$TMP" | head -1)"
check "包含公司分组（华为）" "$(grep -o '华为机试笔试真题' "$TMP" | head -1)"
check "包含公司分组（美团）" "$(grep -o '美团笔试真题' "$TMP" | head -1)"
check "包含公司分组（字节）" "$(grep -o '字节跳动笔试真题' "$TMP" | head -1)"
check "题目链接指向题库目录" "$(grep -oE '(alibaba|huawei|ant|meituan)/[a-z0-9-]+/' "$TMP" | head -1)"
check "GitHub Star 链接正确" "$(grep -o 'https://github.com/cyberspace-cs/zero2Leetcode' "$TMP" | head -1)"
check "不再是目录列表 (autoindex)" "$([ -z "$(grep -o 'Index of /' "$TMP" | head -1)" ] && echo ok)"

echo
echo "== 3. 抽检一篇真题文章 =="
ART="$(grep -oE 'href="[^"]*(alibaba|huawei)/[a-z0-9-]+/"' "$SITE_DIR/04_real_interviews/index.html" | head -1 | sed -E 's/href="([^"]*)"/\1/')"
if [ -n "$ART" ]; then
    ART="${ART#/}"
    ACODE="$(curl -s -o /dev/null -w '%{http_code}' "$BASE/$ART")"
    echo "  $ART -> HTTP $ACODE"
    check "真题文章可访问" "$([ "$ACODE" = "200" ] && echo ok)"
else
    echo "  未能从首页解析出文章链接"
fi

rm -f "$TMP"
echo
echo "结果: $PASS 通过, $FAIL 失败"
[ "$FAIL" -eq 0 ]
