#!/bin/bash
set -euo pipefail
ROOT=$(realpath "${BASH_SOURCE[0]%/*}/..")
CARCH=aarch64
source "$ROOT/pkgbuilds/linux-omarchy-aarch64/PKGBUILD"
[[ " ${pkgname[*]} " == *" linux-omarchy-aarch64-source "* ]]
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
startdir=$scratch/recipe
srcdir=$scratch/inputs
pkgdir=$scratch/package
mkdir -p "$startdir" "$srcdir/$_srcname" "$pkgdir"
cp "$ROOT/pkgbuilds/linux-omarchy-aarch64/PKGBUILD" "$startdir/PKGBUILD"
source=(linux.tar.xz public.patch offline.patch::https://example.invalid/patch)
source_aarch64=(config.aarch64)
for input in "${source[@]}" "${source_aarch64[@]}"; do
  input=${input%%::*}
  echo "$input" > "$srcdir/$input"
done
SRCDEST=$scratch/downloads
mkdir -p "$SRCDEST" "$startdir/keys/pgp"
mv "$srcdir/linux.tar.xz" "$SRCDEST/linux.tar.xz"
echo public-key > "$startdir/keys/pgp/key.asc"
echo config > "$srcdir/$_srcname/.config"
echo release > "$srcdir/$_srcname/version"
echo private > "$srcdir/vendor-firmware.exe"
_package-aarch64-source
cd "$pkgdir/usr/src/$pkgbase"
sha256sum -c SHA256SUMS
[[ -f linux.tar.xz && -f PKGBUILD && -f BUILD_CONFIG && -f KERNEL_RELEASE ]]
[[ -f offline.patch && -f public.patch && -f keys/pgp/key.asc ]]
[[ ! -e vendor-firmware.exe ]]
echo tampered >> offline.patch
if sha256sum -c SHA256SUMS >/dev/null 2>&1; then
  echo 'FAIL: source manifest accepted a modified input'
  exit 1
fi
echo 'PASS: complete declared source inputs and recipe are packaged; unrelated vendor files are excluded'

# Exercise the real kernel package function with a fixture module installer.
# Its ABI marker/release/config paths are consumed by the separate support package.
source "$ROOT/pkgbuilds/linux-omarchy-aarch64/PKGBUILD"
pkgdir=$scratch/kernel-package
srcdir=$scratch/inputs
cd "$srcdir"
mkdir -p "$_srcname/arch/arm64/boot/dts/qcom"
python -c 'import json,sys; print(json.load(open(sys.argv[1]))["kernel_release"])' "$ROOT/pkgbuilds/linux-omarchy-aarch64/a16-source.json" > "$_srcname/version"
echo image > "$_srcname/arch/arm64/boot/Image"
for dtb in glymur-asus-zenbook-a16-ux3607oa x1-fixture hamoa-fixture sc8280xp-fixture; do
  echo dtb > "$_srcname/arch/arm64/boot/dts/qcom/$dtb.dtb"
done
cp "$ROOT/pkgbuilds/linux-omarchy-aarch64/a16-source.json" a16-source.json
make() {
  local modulesdir="$pkgdir/usr/lib/modules/$(<version)"
  mkdir -p "$modulesdir"
  ln -s /fixture-build "$modulesdir/build"
}
_package
release=$(<version)
[[ " ${provides[*]} " == *" omarchy-a16-dsp-abi=1 "* ]]
[[ $(<"$pkgdir/usr/lib/modules/$release/omarchy-a16-dsp-abi") == 1 ]]
[[ $(<"$pkgdir/usr/share/doc/$_kernel/kernel-release") == "$release" ]]
[[ $(<"$pkgdir/usr/lib/modules/$release/pkgbase") == linux-omarchy ]]
cmp .config "$pkgdir/usr/share/doc/$_kernel/config"
cmp ../a16-source.json "$pkgdir/usr/share/doc/$_kernel/a16-source.json"
[[ -f "$pkgdir/boot/dtbs/$_kernel/qcom/glymur-asus-zenbook-a16-ux3607oa.dtb" ]]
echo 'PASS: kernel package publishes the DSP ABI marker, release/config/provenance and model DTB'
