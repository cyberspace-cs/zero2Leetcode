# Build the "code archive" PDF (chapter 5: 06_code_archive) on Windows.
#
# Deliberately split into two stages, because pandoc's startup is extremely slow
# on Windows (antivirus scans the ~233 MB binary on every launch, 24s to 3min),
# while xelatex only takes ~15s:
#
#   1. pandoc  : markdown -> .tex   (slow - run once)
#   2. xelatex : .tex      -> .pdf  (fast - re-run freely while fixing layout)
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-code-pdf.ps1
#
# Optional environment variable:
#   PANDOC   full path to pandoc.exe (default: D:\soft\pandoc\pandoc-3.11\pandoc.exe)
#
# This script is intentionally ASCII-only: Windows PowerShell 5.1 reads .ps1 files
# without a BOM as ANSI, which corrupts non-ASCII string literals.

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pandoc   = if ($env:PANDOC) { $env:PANDOC } else { 'D:\soft\pandoc\pandoc-3.11\pandoc.exe' }
$work     = Join-Path $repoRoot 'tmp\pdfs'
$stage    = Join-Path $work 'stage'
$texName  = 'code-archive.tex'
$outName  = 'zero2Leetcode-code-archive-v0.1.0.pdf'

Write-Host "repo root: $repoRoot"
Write-Host "pandoc:    $pandoc"

if (-not (Test-Path $pandoc)) {
    throw "pandoc not found: $pandoc (set the PANDOC environment variable to override)"
}

New-Item -ItemType Directory -Force -Path $work, $stage | Out-Null
Set-Location $repoRoot

# --------------------------------------------------------------- 1) assemble markdown
Write-Host ""
Write-Host "[1/3] assembling chapter 5 markdown ..."
& py 'publish-pdf\prepare.py' --repo-root . --output-dir $stage --chapters 5
if ($LASTEXITCODE -ne 0) { throw "prepare.py failed" }

# --------------------------------------------------------------- 2) pandoc -> tex
Write-Host ""
Write-Host "[2/3] pandoc -> LaTeX (slow, this can take several minutes, do NOT interrupt) ..."
$inputs = @(
    (Join-Path $stage '00-preface.md'),
    (Join-Path $stage '05-code-archive.md')
)
$texPath = Join-Path $work $texName
$texLog  = Join-Path $work 'pandoc.log'
Remove-Item $texPath, $texLog -Force -ErrorAction SilentlyContinue

$pandocArgs = $inputs + @(
    '--from=markdown+raw_html+tex_math_dollars',
    '--to=latex',
    '--standalone',
    '--template=publish-pdf/templates/bluebook.tex',
    '--metadata-file=publish-pdf/templates/metadata.yaml',
    "--resource-path=.;$stage;publish-pdf/templates",
    '--toc',
    '--toc-depth=2',
    '--number-sections',
    '--top-level-division=chapter',
    '--syntax-highlighting=none',
    '-o', $texPath
)

$sw = [Diagnostics.Stopwatch]::StartNew()
& $pandoc @pandocArgs 2>&1 | Out-File -FilePath $texLog -Encoding UTF8
$sw.Stop()
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $texPath)) {
    Write-Host "pandoc failed, log tail:"
    Get-Content $texLog -Tail 30
    throw "pandoc failed to produce LaTeX"
}
Write-Host ("      -> {0} ({1:N0} bytes, {2}s)" -f $texName, (Get-Item $texPath).Length, [int]$sw.Elapsed.TotalSeconds)

# --------------------------------------------------------------- 3) xelatex -> pdf
# xelatex MUST run with cwd = repo root, because bluebook.tex references assets
# by relative path (e.g. book/assets/....png). The .tex lives in tmp/pdfs, so pass
# it as a relative path with FORWARD slashes (TeX eats backslashes), and send all
# output back into tmp/pdfs via -output-directory so the repo root stays clean.
$workFwd = $work -replace '\\', '/'
$relTex  = 'tmp/pdfs/' + $texName

Write-Host ""
Write-Host "[3/3] xelatex (two passes so the table of contents resolves) ..."
foreach ($pass in 1, 2) {
    & xelatex -interaction=nonstopmode -halt-on-error "-output-directory=$workFwd" $relTex *> (Join-Path $work "xelatex-pass$pass.log")
    Write-Host "      pass$pass exit=$LASTEXITCODE"
}

$builtPdf = Join-Path $work 'code-archive.pdf'
if (-not (Test-Path $builtPdf)) {
    Write-Host ""
    Write-Host "compile failed, log tail:"
    Get-Content (Join-Path $work 'xelatex-pass2.log') -Tail 30
    throw "xelatex did not produce a PDF"
}

# publish into downloads/
$destPdf = Join-Path $repoRoot ("downloads\" + $outName)
Copy-Item $builtPdf $destPdf -Force

$missing = (Select-String -Path (Join-Path $work 'xelatex-pass2.log') -Pattern 'Missing character' | Measure-Object).Count
if ($missing -gt 0) {
    Write-Host ""
    Write-Host "WARNING: $missing missing-glyph warnings - some characters have no font. Check the CJK fonts in bluebook.tex."
}

Write-Host ""
Write-Host "=== done ==="
Write-Host "PDF: $destPdf"
pdfinfo $destPdf | Select-Object -First 10
Write-Host ""
Write-Host "next: refresh the download manifest"
Write-Host "  py scripts/sync-downloads.py"
