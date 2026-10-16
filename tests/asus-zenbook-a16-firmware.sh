#!/bin/bash
set -euo pipefail
repo=$(realpath "${BASH_SOURCE[0]%/*}/..")
source "$repo/pkgbuilds/asus-zenbook-a16-firmware/activate-calibration"
fixture=$(mktemp -d)
trap 'rm -rf "$fixture"' EXIT
compatible=$fixture/compatible
source=$fixture/package/board.bin
destination=$fixture/root/updates/ath12k/QCC2072/hw1.0/board.bin
mkdir -p "${source%/*}"
printf 'packaged-calibration' > "$source"
printf 'lenovo,yoga-slim7x\0' > "$compatible"
activate_calibration "$compatible" "$source" "$destination"
[[ ! -e $destination ]]
for name in asus,zenbook-a16-ux3607oa asus,ux3607oa; do
  printf '%s\0qcom,glymur\0' "$name" > "$compatible"
  activate_calibration "$compatible" "$source" "$destination"
  [[ -L $destination && $(readlink "$destination") == "$source" ]]
  activate_calibration "$compatible" "$source" "$destination"
  printf 'updated-package-calibration' > "$source"
  [[ $(cat "$destination") == updated-package-calibration ]]
  rm "$destination"
done
cp "$source" "$destination"
activate_calibration "$compatible" "$source" "$destination"
[[ -L $destination ]]
rm "$destination"
printf 'existing-user-calibration' > "$destination"
if activate_calibration "$compatible" "$source" "$destination"; then
  echo 'Unknown calibration was overwritten' >&2; exit 1
fi
[[ $(cat "$destination") == existing-user-calibration ]]
rm "$destination"
ln -s "$fixture/user-override" "$destination"
if activate_calibration "$compatible" "$source" "$destination"; then
  echo 'An existing override was replaced' >&2; exit 1
fi
[[ $(readlink "$destination") == "$fixture/user-override" ]]
rm "$destination" "$source"
if activate_calibration "$compatible" "$source" "$destination"; then
  echo 'Missing package data was accepted' >&2; exit 1
fi
printf 'ASUS_A16_MODEL_GATE_CALIBRATION_UPGRADE_AND_OVERRIDE_TEST_PASS\n'
