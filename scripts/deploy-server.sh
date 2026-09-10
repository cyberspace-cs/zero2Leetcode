#!/usr/bin/env bash
#
# zero2Leetcode —— 服务器端构建 & 发布脚本
#
# 作用：把 Jekyll 源码构建成纯静态站点（_site），供 nginx 直接托管。
#       onefly.top/zero2Leetcode 线上页面就是这么渲染出来的，所以这里
#       用同一套 Jekyll + _layouts/default.html + assets/css/docs.css，
#       保证生成的页面与线上完全一致。
#
# 在 Ubuntu 服务器上以普通用户运行（需要能免密用 docker，以及 nginx reload 权限）。
#
# 用法：
#   bash scripts/deploy-server.sh              # 构建 + 发布
#   SKIP_PULL=1 bash scripts/deploy-server.sh  # 跳过 git pull，只重新构建
#
set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/ubuntu/shuati-coach/zero2Leetcode}"
SITE_DIR="${SITE_DIR:-$REPO_DIR/_site}"
DOMAIN="${DOMAIN:-zero2leetcode.taoxie.vip}"
NGINX_CONF="${NGINX_CONF:-/etc/nginx/sites-available/zero2Leetcode-domain}"

# baseurl 必须为空：站点是通过 https://<域名>/ 根路径访问的，
# 而 _config.yml 里的 baseurl: /zero2Leetcode 是给 onefly.top 子目录用的。
SITE_BASEURL="${SITE_BASEURL:-}"

log() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }

log "仓库目录: $REPO_DIR"
cd "$REPO_DIR"

# ---------------------------------------------------------------------------
# 1) 同步源码
# ---------------------------------------------------------------------------
if [ "${SKIP_PULL:-0}" != "1" ]; then
    log "同步 GitHub 源码"
    git fetch origin --prune
    git reset --hard origin/main
fi

# ---------------------------------------------------------------------------
# 2) 清理会与 Jekyll 生成页面冲突的手写 HTML
#    04_real_interviews/index.md 与 05_interview/index.md 是页面源文件，
#    同目录下的 index.html 会覆盖/冲突，必须移除。
# ---------------------------------------------------------------------------
for f in 04_real_interviews/index.html 05_interview/index.html; do
    if [ -f "$f" ]; then
        log "移除冲突文件 $f"
        rm -f "$f"
    fi
done

# ---------------------------------------------------------------------------
# 3) 用 Jekyll 构建
#    服务器已通过 apt 安装 ruby-full + jekyll，并额外 gem install jekyll-sitemap
#    （_config.yml 里声明了该插件）。
#    若想改用 Docker，设置 JEKYLL_CMD 覆盖，例如：
#      JEKYLL_CMD="docker run --rm -v \$PWD:/srv/jekyll -w /srv/jekyll jekyll/jekyll:4.2.2 jekyll" \
#        bash scripts/deploy-server.sh
# ---------------------------------------------------------------------------
log "构建静态站点 (baseurl='$SITE_BASEURL')"
rm -rf "$SITE_DIR"

if ! command -v jekyll >/dev/null 2>&1; then
    echo "未找到 jekyll，请先执行：" >&2
    echo "  sudo apt-get install -y ruby-full jekyll build-essential" >&2
    echo "  sudo gem install jekyll-sitemap --no-document" >&2
    exit 1
fi

JEKYLL_ENV=production jekyll build --baseurl "$SITE_BASEURL" --destination "$SITE_DIR" --trace

if [ ! -d "$SITE_DIR" ]; then
    echo "构建失败：未生成 $SITE_DIR" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 4) 构建结果自检
# ---------------------------------------------------------------------------
log "校验关键产物"
for f in index.html \
         04_real_interviews/index.html \
         05_interview/index.html \
         assets/css/docs.css; do
    if [ -s "$SITE_DIR/$f" ]; then
        printf '  \033[1;32m✓\033[0m %s\n' "$f"
    else
        printf '  \033[1;31m✗\033[0m %s (缺失)\n' "$f" >&2
        exit 1
    fi
done

# ---------------------------------------------------------------------------
# 5) nginx 指向 _site 并重载
# ---------------------------------------------------------------------------
log "更新 nginx root -> $SITE_DIR"
if [ -f "$NGINX_CONF" ]; then
    if grep -q "root $SITE_DIR;" "$NGINX_CONF"; then
        log "nginx root 已是 $SITE_DIR，跳过修改"
    else
        sudo -n cp "$NGINX_CONF" "$NGINX_CONF.bak.$(date +%Y%m%d%H%M%S)"
        sudo -n sed -i -E "s#^([[:space:]]*)root .*;#\1root $SITE_DIR;#" "$NGINX_CONF"
        # 关掉目录列表：源码目录才会 autoindex，静态站点不需要
        sudo -n sed -i -E "s#^([[:space:]]*)autoindex on;#\1autoindex off;#" "$NGINX_CONF"
    fi
    sudo -n nginx -t
    sudo -n systemctl reload nginx
else
    echo "未找到 $NGINX_CONF，请手动把 root 指向 $SITE_DIR" >&2
fi

log "发布完成 -> http://$DOMAIN/"
