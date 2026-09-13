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
echo "== 4. 代码库 & ACM 题解页 =="
ARCH="$BASE/06_code_archive/index.html"
TMP2="$(mktemp)"
ACODE="$(curl -s -o "$TMP2" -w '%{http_code}' "$ARCH")"
echo "  HTTP $ACODE, $(wc -c <"$TMP2") bytes"
check "代码库页返回 200" "$([ "$ACODE" = "200" ] && echo ok)"
check "渲染了下载中心" "$(grep -o '下载中心' "$TMP2" | head -1)"
check "渲染了 ACM 题解索引" "$(grep -o 'ACM 题解索引' "$TMP2" | head -1)"
check "渲染了本地代码库" "$(grep -o '本地代码库' "$TMP2" | head -1)"
check "ACM 题目已入索引" "$(grep -o 'CF 4A Watermelon' "$TMP2" | head -1)"
check "代码库文件已入索引" "$(grep -o 'lc_0206_reverse-linked-list.py' "$TMP2" | head -1)"
check "外部仓库条目已入索引" "$(grep -o 'leetcode/ACM-lc/HOT100' "$TMP2" | head -1)"
check "外部仓库题名已渲染" "$(grep -o '最长连续序列' "$TMP2" | head -1)"
check "下载表含完整 SHA-256" \
    "$(grep -o '026901c393dad5a0b87d0cd9a826d7f1885db27d4ce5d4d80b5969e32c9941d9' "$TMP2" | head -1)"
check "侧边栏已加入新模块" "$(grep -o '06_code_archive' "$TMP2" | head -1)"

echo
echo "== 5. 下载资产可达性 =="
for f in zero2Leetcode-bluebook-v0.1.0-full.pdf \
         zero2Leetcode-bluebook-v0.1.0-high-frequency.pdf \
         zero2Leetcode-bluebook-v0.1.0.zip \
         zero2Leetcode-my-solutions-v0.1.0.zip \
         zero2Leetcode-code-archive-v0.1.0.pdf; do
    code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE/downloads/$f")"
    printf '  %-52s HTTP %s\n' "$f" "$code"
    check "可下载 $f" "$([ "$code" = "200" ] && echo ok)"
done

echo
echo "== 6. ACM 题解文章 =="
PCODE="$(curl -s -o /dev/null -w '%{http_code}' "$BASE/06_code_archive/problems/cf-4a-watermelon/")"
echo "  HTTP $PCODE"
check "ACM 题解文章可访问" "$([ "$PCODE" = "200" ] && echo ok)"

rm -f "$TMP2"
echo
echo "结果: $PASS 通过, $FAIL 失败"
[ "$FAIL" -eq 0 ]
