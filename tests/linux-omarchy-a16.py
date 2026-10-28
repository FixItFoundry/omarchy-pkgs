#!/usr/bin/env python3
"""Check recipe integrity and the release/ABI contract without downloading Linux."""
import hashlib
import json
from pathlib import Path
import subprocess

recipe = Path(__file__).resolve().parents[1] / 'pkgbuilds/linux-omarchy-aarch64'
keys = ['source', 'source_aarch64', 'sha256sums', 'sha256sums_aarch64',
        'b2sums', 'b2sums_aarch64', 'pkgname']
command = 'CARCH=aarch64; source "$1"; '
for key in keys:
    command += 'printf "%s\\0" "${' + key + '[@]}"; printf "\\1"; '
command += 'printf "%s\\0" "$pkgver" "$pkgrel"'
parts = subprocess.check_output(['bash', '-c', command, 'bash', str(recipe / 'PKGBUILD')]).split(b'\1')
arrays = {key: [v.decode() for v in part.split(b'\0') if v] for key, part in zip(keys, parts)}
version, revision = [v.decode() for v in parts[-1].split(b'\0') if v]
manifest = json.loads((recipe / 'a16-source.json').read_text())
assert manifest['kernel_version'] == version
assert manifest['package_revision'] == int(revision)
upstream_version = version + '.0' if version.count('.') == 1 else version
assert manifest['kernel_release'] == f'{upstream_version}-{revision}-omarchy'
assert manifest['a16_dsp_abi'] == 1
assert len(manifest['source_tree']) == 40
assert arrays['pkgname'] == ['linux-omarchy', 'linux-omarchy-headers', 'linux-omarchy-aarch64-source']
count = 0
for suffix in ['', '_aarch64']:
    sources = arrays['source' + suffix]
    for key, algorithm in [('sha256sums', hashlib.sha256), ('b2sums', hashlib.blake2b)]:
        sums = arrays[key + suffix]
        assert len(sources) == len(sums), (key, suffix, len(sources), len(sums))
        for source, expected in zip(sources, sums):
            if source.startswith('https://'):
                continue
            if expected == 'SKIP':
                assert source.endswith('.sig'), source
                continue
            assert algorithm((recipe / source).read_bytes()).hexdigest() == expected, source
    count += len(sources)
patches = [p for p in arrays['source'] if p.endswith('.patch')]
assert len(patches) == manifest['total_patch_count'] == manifest['shared_patch_count'] + 3
assert not any(p.startswith('2502-') for p in patches)
assert len({p.split('-', 1)[0] for p in patches}) == len(patches)
assert '2302-ASoC-codecs-lpass-wsa-macro-switch-cache-to-REGCACHE.patch' in patches
assert '2434-arm64-dts-qcom-surface-laptop8-Disable-the-Wi-Fi-har.patch' in patches
assert all(p.startswith(('2500-', '2501-', '2503-')) for p in manifest['local_patch_sha256'])
assert '2300-glymur-asus-zenbook-a16-board-support.patch' not in patches
assert '2210-arm64-dts-qcom-hamoa-glymur-Disable-the-crypto-engine.patch' in patches
for patch, expected in manifest['local_patch_sha256'].items():
    assert patch in patches
    assert hashlib.sha256((recipe / patch).read_bytes()).hexdigest() == expected
print(f'PASS: {count} declared inputs, aligned checksums, {len(patches)} patches and matching source/release/ABI metadata')
