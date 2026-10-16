# A16 support in the shared ARM kernel

This remains Omarchy's `linux-omarchy-aarch64` recipe and produces `linux-omarchy` and `linux-omarchy-headers`. The base is kernel.org 7.2.10, with the existing Omarchy scheduler and ARM/N1x patches rebased, then the A16 board backport. `A16-REBASE.json` records the complete expected source tree, patches already present in stable, and shared patches requiring rebasing. The Omarchy HID implementation is retained in place of the older duplicate A16 keyboard patches.

The upstream tarball signature is verified normally. Unchanged shared patch signatures are retained; modified patch bytes have new SHA256/BLAKE2 checksums and no reused signature. `prepare()` checks the complete patched Git tree before generating localversion/config files. `check()` verifies the built release, A16 DTB, SoundWire keep-awake properties and explicit board configuration.

The kernel provides `omarchy-a16-dsp-abi=1` and installs a per-release marker. Keep that capability only while the early DSP interface and required module names remain compatible with `omarchy-a16-support`. Kernel version updates do not require changing a support-package version pin. Audit the new source, rebuild both kernel and matching headers, run the package/boot checks, and publish through the normal signed repository. Do not automatically synchronize this audited recipe from an unrelated upstream recipe.

The support package contains public topology/UCM and boot checks; signed machine firmware and Wi-Fi calibration are obtained locally. The ISO is built with the normal shared ARM entrypoint and package bundle. Hardware acceptance and a snapshot restore remain required before declaring this board upgrade-tested.
