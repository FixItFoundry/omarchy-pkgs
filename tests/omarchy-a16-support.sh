#!/bin/bash
set -euo pipefail
repo=$(realpath "${BASH_SOURCE[0]%/*}/..")
fixture=$(mktemp -d)
trap 'rm -rf "$fixture"' EXIT
srcdir=$fixture/src
pkgdir=$fixture/package
mkdir -p "$srcdir" "$pkgdir"
source "$repo/pkgbuilds/omarchy-a16-support/PKGBUILD"
printf '%s  %s\n' "${sha256sums[0]}" "$repo/pkgbuilds/omarchy-a16-support/support.tar.xz" | sha256sum -c
tar -xf "$repo/pkgbuilds/omarchy-a16-support/support.tar.xz" -C "$srcdir"
package
cmp "$srcdir/support/51-glymur-ucm.conf" "$pkgdir/usr/share/omarchy-a16/51-glymur-ucm.conf"
[[ ! -e $pkgdir/usr/share/wireplumber && ! -e $pkgdir/etc/wireplumber ]]
echo 'PASS: support package keeps A16 audio policy inactive until model-gated setup'
