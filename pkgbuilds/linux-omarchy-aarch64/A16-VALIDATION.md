# Linux 7.3-5 A16 rebase validation

Baseline: `omacom/omarchy-pkgs@a8de4a65abd6bf0bfd90fa515d2f160ca280c973`, including the Surface Laptop 8 merge (#1706) at `488cd623d066eab6ad3cf07774a84d1596b697b9`.
Previous PR head: `026ad947ce51dadccc25f4dde5ba7db31a5f584f`.
Candidate: package `7.3-5`, kernel `7.3.0-5-omarchy`.
Patched source tree: `035c9c08d096b1762f937a942ce9d3c17f2e392e`.

Checks ran on 27 October 2026 in an isolated Arch Linux ARM container on an AArch64 Debian VM, using GCC 16.1.1, binutils 2.46.0 and GNU Make 4.4.1. These are native source/object checks; the full kernel/headers/source package build and physical A16 acceptance remain pending.

| Check | Actual result |
| --- | --- |
| Source archive SHA-256 and BLAKE2 | Match the unchanged shared recipe |
| Linux archive OpenPGP signature | Good signature from the pinned Greg Kroah-Hartman key `647F28654894E3BD457199BE38DBBDC86092693E` |
| Shared detached patch signatures | All 76 verify using the supplied public keys |
| Shared stack preservation | All 357 shared patches, input order, checksums, signatures and `config.aarch64` are unchanged |
| Recipe integrity | 443 declared inputs; aligned SHA-256/BLAKE2 arrays and local input checksums pass |
| Patch application | All 360 patches apply to the signed 7.3 archive with zero fuzz and no rejects; offsets allowed |
| Distributed-source replay | Real `makepkg --verifysource` and `makepkg --nobuild --nodeps` pass from the staged corresponding-source package; its complete patched source tree matches the recorded hash |
| Configuration/release | Every unchanged A16 overlay setting survives native `olddefconfig`; actual recipe release check passes for `7.3.0-5-omarchy` |
| Device trees | Both A16 and Surface Laptop 8 DTBs compile; decompiled A16 DTB has exactly two `qcom,keep-runtime-active` properties |
| Native compilation | All 54 changed C files plus block-mq/mq-deadline, shared eDP, adjacent DP panel/link, dwc3-qcom and the shared USB4 host compile: 61 AArch64 ELF objects with no compiler warnings/errors in the final checks |
| Compiled regressions | Battery missing-property/EAGAIN, valid-property, transport and allocation failures pass; actual merged QMP cleanup/rollback code passes reset/regulator retry, reference-count, forced cleanup, failed USB/USB4 initialization and Type-C rollback success/failure cases under mocks |
| Source contracts | Deferred SoundWire bus/DAI error handling, upstream block-mq initialization, DSP early-boot/shared-memory bridge and board policy checks pass |
| Packaging regressions | Source inputs, aliases, external download cache, public keys and tamper detection pass; kernel fixture installs ABI provider/marker, actual release, config, provenance and DTBs |
| Corresponding-source staging | Real recipe/inputs/config/release stage successfully; all 449 manifest entries verify |
| Repository checks | Package metadata and pinned-source tests pass |

## Overlap resolution

A three-way comparison used the previous 222-patch shared baseline, the previous A16 source changes and the new 357-patch shared baseline. Sixteen files overlap; five require manual resolution. The A16 patches move from 2300/2301/2303 to 2500/2501/2503. SoundWire and battery patch contents are unchanged.

The LPASS Compander1 addresses, Glymur USB votes, v8 eDP calibration and `LINK_RATE_SET` fixes are supplied by the shared series. The newer eDP driver remains byte-for-byte identical to the shared baseline. The remaining QMP merge keeps shared USB4 precedence, DP lane selection, deferred native-mode requests, calibration and the runtime-PM guard while adapting the prior A16 resource tracking and rollback checks. Display merges preserve shared FEC/USB4 paths and A16 transfer/error cleanup. Altmode stores the masked V2 mux value in its synchronized snapshot and returns invalid cable errors to the acknowledging worker.

The first native object pass caught four invalid-cable exits inherited from the shared void helpers after merging them into A16 error-returning helpers. They now return `-EINVAL`. A later caller audit also found that failed USB/USB4 initialization could retain a tentative PHY reference when reset cleanup failed. Both failure callers now release that reference while keeping failed resources tracked. A compiled regression fails on the earlier candidate and passes with the corrected callers. The final native object checks and compiled regressions pass after these corrections.

Native `olddefconfig` regenerates compiler/tool capability and BTF-related settings for the installed tools. All A16 overlay settings survive; the shared config input is unchanged. This does not establish the full Arch BTF/module build. `makepkg --nodeps` was used only for source preparation, not to claim a completed package build. Source-package staging and kernel-package fixtures do not substitute for real split-package archives.

## Required before promotion

- Build all three split packages with the complete supported native Arch aarch64 build dependencies; run full `build()`/`check()`, module/symbol checks and packaged-header module compilation.
- Retain the matching corresponding-source package and verify its final release artifacts through the normal publishing pipeline.
- Boot both UKIs on a physical A16; verify release/ABI markers, both early DSPs before root mount, firmware selection and absence of early modprobe or battery uevent failures.
- Recheck audio playback/microphones, deferred codec reset/recovery, internal display, external outputs/hotplug and failed-link/power transitions.
- Recheck charger/battery transitions, Wi-Fi, Bluetooth calls/audio, keyboard, touchscreen, USB and storage; reassess PMIC supplier-link and codec warnings.
- Run shared-kernel regressions on the other ARM boards, including Surface Laptop 8 after these driver merges.

Earlier A16 hardware acceptance remains historical evidence for **7.2.8-24** only. The previous 7.3-4 checks remain source/cross-compilation evidence. Camera and sleep receive no new acceptance claim. No OEM firmware, external-SSD UAS quirk or `omarchy-a16-support` recipe is added here.
