# A16 additions to the shared ARM kernel

This contribution targets `omacom/omarchy-pkgs@a8de4a65`, after the Surface Laptop 8 merge (#1706), and advances `pkgrel=4` to `5`. The package version is **7.3-5**; the kernel release is **7.3.0-5-omarchy**. All 357 shared patches, signatures, checksums and `config.aarch64` are retained. The shared Type-C/USB4 configuration and existing kernel/headers package names stay in place. The separate `omarchy-a16-support` recipe is outside this contribution.

- **2500:** residual A16 hardware fixes after the complete shared series. The shared LPASS Compander1 addresses, Glymur USB votes, v8 eDP calibration and `LINK_RATE_SET` fixes are no longer duplicated. A16 board power/firmware policy, EC, audio, display recovery, Wi-Fi, camera prerequisites and error handling remain. Camera nodes stay disabled.
- **2501:** deferred SoundWire codecs, renumbered from 2301 with unchanged contents. The bus remains registered while reset suppliers finish probing.
- **2503:** temporary `-EAGAIN` battery properties are omitted from uevents, renumbered from 2303 with unchanged contents. Direct reads and other errors keep their behavior.

The original A16 block-mq patch remains omitted because Linux 7.3 includes it. Shared patch 2302 is a different LPASS regcache change and is retained.

The QMP merge retains shared USB4 ownership, deferred native-mode requests, DP lane selection, runtime-PM guard and calibration. A16 clock/regulator/reset tracking, failed-transition rollback and powered-off access checks are adapted to that state machine. DP retains the shared FEC/USB4 paths and A16 transfer/error cleanup. Altmode retains masked V2 notifications, synchronized snapshots and firmware acknowledgments, including invalid cable errors.

`a16-source.json` pins the baseline, complete patched source-tree hash and local patch digests. `prepare()` checks source regressions, provenance, configuration and the actual kernel release. `check()` requires the Image, module symbol table and A16 DTB with its two SoundWire runtime-active properties. The unchanged `a16.config` remains an overlay on the shared config.

The package provides `omarchy-a16-dsp-abi=1`, installs its per-release marker, and records the actual kernel release, configuration and source provenance. The SoCCP early-boot/shared-memory bridge contract is retained. The ABI marker is an interface contract; it does not establish physical A16 acceptance.

See [A16-VALIDATION.md](A16-VALIDATION.md) for current checks and remaining gates. Earlier native package, UKI and physical results belong to **7.2.8-24-omarchy**. Camera and sleep remain outside the validated A16 scope. Other ARM boards require fresh regression coverage.

## Corresponding source publication

The split build emits `linux-omarchy-aarch64-source` alongside kernel and headers. It includes every declared archive, patch, config, regression helper and signature, public keys, the actual recipe, final `BUILD_CONFIG`, `KERNEL_RELEASE` and `SHA256SUMS`. Publish and retain all three matching outputs through the existing artifact/signing pipeline. `README.source` describes offline preparation; `.BUILDINFO` records native build dependencies. Source reconstruction does not guarantee identical binaries across toolchains. No OEM firmware is included.
