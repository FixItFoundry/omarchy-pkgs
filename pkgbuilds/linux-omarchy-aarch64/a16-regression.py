#!/usr/bin/env python3
"""Source regressions for the shared kernel's A16 contracts (no hardware needed)."""
from pathlib import Path
import os
import re
import shlex
import subprocess
import sys
import tempfile


def function(text, name):
    match = re.search(r"(?:static )?(?:int|void|bool) " + name + r"\([^;]*?\)\n\{", text)
    if not match:
        raise AssertionError(f"Missing function: {name}")
    start = text.index("{", match.start())
    # Kernel functions end at column zero; this also handles #ifdef branches.
    end = re.search(r"^}", text[start:], re.M)
    if not end:
        raise AssertionError(f"Unterminated function: {name}")
    return text[match.start():start + end.end()]



def check(root):
    read = lambda path: (root / path).read_text()
    swr = read("drivers/soundwire/qcom.c")
    probe = function(swr, "qcom_swrm_probe")
    assert "boot enumeration pending: allowing deferred codec probes" in probe
    assert 'if (qcom_swrm_all_slaves_online(ctrl))' in probe
    assert "ret = -ETIMEDOUT" not in probe
    assert re.search(r"ret = qcom_swrm_register_dais\(ctrl\);\s*if \(ret\)\s*goto err_master_add;", probe)
    assert '"qcom,keep-runtime-active"' in probe

    # This fix is supplied by Linux 7.3, not another downstream patch.
    blk = read("block/blk-mq.c")
    late = function(blk, "blk_mq_rq_late_init")
    assert "blk_op_bypass_sched(rq->cmd_flags)" in late
    assert "RQF_SCHED_TAGS" in late and "RQF_RESV" in late
    assert "rq->rq_flags |= RQF_USE_SCHED" in late
    assert "e->type->ops.prepare_request(rq)" in late
    assert "RQF_USE_SCHED" not in function(blk, "blk_mq_limit_depth")

    pas = read("drivers/remoteproc/qcom_q6v5_pas.c")
    soccp = re.search(r"glymur_soccp_resource = \{(.*?)\n\};", pas, re.S).group(1)
    assert ".early_boot = true" in soccp and ".needs_tzmem = true" in soccp
    board = read("arch/arm64/boot/dts/qcom/glymur-asus-zenbook-a16-ux3607oa.dts")
    assert board.count("qcom,keep-runtime-active;") == 2

    # Compile the actual patched uevent helper, with only its environment mocked.
    helper = function(read("drivers/power/supply/power_supply_sysfs.c"), "add_prop_uevent")
    harness = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <string.h>
struct device { int unused; };
struct kobj_uevent_env { int unused; };
struct device_attribute { int unused; };
enum power_supply_property { PROP_TEST };
struct power_supply_attr { struct device_attribute dev_attr; const char *prop_name; };
static struct power_supply_attr power_supply_attrs[] = {{{0}, "STATUS"}};
static int property_result, event_result, event_calls;
static int power_supply_format_property(struct device *dev, bool uevent,
    struct device_attribute *attr, char *buf) {
    (void)dev; (void)uevent; (void)attr;
    if (property_result >= 0) strcpy(buf, "Charging\n");
    return property_result;
}
static int add_uevent_var(struct kobj_uevent_env *env, const char *fmt,
    const char *name, const char *value) {
    (void)env; (void)fmt; (void)name;
    assert(strcmp(value, "Charging") == 0);
    event_calls++;
    return event_result;
}
'''
    cases = r'''
int main(void) {
    char buf[64]; struct device dev = {0}; struct kobj_uevent_env env = {0};
    int missing[] = {-ENODEV, -ENODATA, -EINVAL, -EAGAIN};
    for (unsigned i = 0; i < sizeof(missing)/sizeof(missing[0]); i++) {
        property_result = missing[i]; event_calls = 0;
        assert(add_prop_uevent(&dev, &env, PROP_TEST, buf) == 0);
        assert(event_calls == 0);
    }
    int errors[] = {-EIO, -ENOMEM, -ETIMEDOUT};
    for (unsigned i = 0; i < sizeof(errors)/sizeof(errors[0]); i++) {
        property_result = errors[i]; event_calls = 0;
        assert(add_prop_uevent(&dev, &env, PROP_TEST, buf) == errors[i]);
        assert(event_calls == 0);
    }
    property_result = 9; event_result = 0; event_calls = 0;
    assert(add_prop_uevent(&dev, &env, PROP_TEST, buf) == 0);
    assert(event_calls == 1);
    event_result = -ENOMEM;
    assert(add_prop_uevent(&dev, &env, PROP_TEST, buf) == -ENOMEM);
    return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix="a16-regression-") as tmp:
        source = Path(tmp) / "battery.c"
        binary = Path(tmp) / "battery"
        source.write_text(harness + helper + cases)
        subprocess.run(shlex.split(os.environ.get("HOSTCC", "cc")) +
                       ["-std=c11", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print("PASS: deferred SoundWire, upstream block-mq, DSP/DT contracts and compiled battery uevent regression")


    # Exercise the merged QMP cleanup and rollback code with failing resources.
    qmp = read("drivers/phy/qualcomm/phy-qcom-qmp-combo.c")
    helper = function(qmp, "qmp_combo_com_exit")
    rollback = function(qmp, "qmp_combo_reconfigure_phy")
    harness = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#define BIT(n) (1UL << (n))
#define dev_err(...) ((void)0)
#define dev_err_probe(dev, error, ...) (error)
#define WARN_ON(condition) ((void)(condition))
#define guard(kind) mock_guard
enum typec_orientation { NORMAL, REVERSE };
enum qmpphy_mode { NATIVE, USB4 };
#define QMPPHY_MODE_USB4 USB4
struct regulator { int index; };
struct regulator_bulk_data { struct regulator *consumer; };
struct qmp_phy_cfg { int num_vregs, num_resets; bool configure_usb4_phy; };
struct qmp_combo {
    const struct qmp_phy_cfg *cfg;
    struct regulator_bulk_data *vregs;
    int init_count, num_clks, resets, pipe_clk, clks, phy_mutex;
    unsigned int usb_init_count, usb4_init_count, usb4_rx_eq;
    int p2rr2p_pipe_clk;
    unsigned long vregs_enabled;
    bool com_powered_on, reset_pending, pipe_clk_enabled, clks_enabled;
    enum typec_orientation orientation;
    enum qmpphy_mode qmpphy_mode;
    struct phy *usb_phy;
};
static int reset_error, regulator_error = -1, pipe_disables, clock_disables;
static int reset_control_bulk_assert(int n, int resets) {
    (void)n; (void)resets; return reset_error;
}
static void clk_disable_unprepare(int c) { (void)c; pipe_disables++; }
static void clk_bulk_disable_unprepare(int n, int c) {
    (void)n; (void)c; clock_disables++;
}
static int regulator_disable(struct regulator *r) {
    return r->index == regulator_error ? -EIO : 0;
}
struct phy { struct qmp_combo *qmp; };
static void mock_guard(int *lock) { (void)lock; }
static struct qmp_combo *phy_get_drvdata(struct phy *phy) { return phy->qmp; }
static int clk_prepare_enable(int clock) { (void)clock; return 0; }
static int qmp_combo_com_init(struct qmp_combo *qmp, bool force) {
    assert(!force); qmp->init_count++; return 0;
}
static int qmp_combo_usb_power_on(struct phy *phy) { (void)phy; return -EIO; }
static int apply_calls, apply_error, rollback_error;
static int qmp_combo_apply_mode(struct qmp_combo *qmp, enum qmpphy_mode mode) {
    apply_calls++;
    qmp->qmpphy_mode = mode;
    if (apply_calls == 2) {
        assert(qmp->orientation == NORMAL);
        assert(mode == NATIVE);
        return rollback_error;
    }
    assert(qmp->orientation == REVERSE);
    return apply_error;
}
'''
    cases = r'''
int main(void) {
    struct qmp_phy_cfg cfg = { .num_vregs = 2 };
    struct regulator regs[] = {{0}, {1}};
    struct regulator_bulk_data bulk[] = {{&regs[0]}, {&regs[1]}};
    struct qmp_combo q = {
        .cfg = &cfg, .vregs = bulk, .init_count = 1, .vregs_enabled = 3,
        .com_powered_on = true, .reset_pending = true,
        .pipe_clk_enabled = true, .clks_enabled = true
    };
    reset_error = -ETIMEDOUT;
    assert(qmp_combo_com_exit(&q, false) == -ETIMEDOUT);
    assert(q.init_count == 1 && q.reset_pending && q.vregs_enabled == 3);
    assert(!pipe_disables && !clock_disables);
    reset_error = 0; regulator_error = 0;
    assert(qmp_combo_com_exit(&q, false) == -EIO);
    assert(q.init_count == 1 && q.vregs_enabled == 1 && !q.com_powered_on);
    assert(pipe_disables == 1 && clock_disables == 1);
    regulator_error = -1;
    assert(qmp_combo_com_exit(&q, false) == 0);
    assert(q.init_count == 0 && q.vregs_enabled == 0);
    assert(pipe_disables == 1 && clock_disables == 1);
    assert(qmp_combo_com_exit(&q, false) == -EINVAL);
    q.init_count = 2;
    assert(qmp_combo_com_exit(&q, false) == 0 && q.init_count == 1);
    assert(qmp_combo_com_exit(&q, true) == 0 && q.init_count == 1);
    apply_error = -EIO; rollback_error = 0;
    assert(qmp_combo_reconfigure_phy(&q, REVERSE, USB4) == -EIO);
    assert(apply_calls == 2 && q.orientation == NORMAL && q.qmpphy_mode == NATIVE);
    apply_calls = 0; rollback_error = -ETIMEDOUT; q.com_powered_on = true;
    assert(qmp_combo_reconfigure_phy(&q, REVERSE, USB4) == -EIO);
    assert(!q.com_powered_on && q.orientation == NORMAL && q.qmpphy_mode == NATIVE);
    apply_calls = 0; apply_error = 0;
    assert(qmp_combo_reconfigure_phy(&q, REVERSE, USB4) == 0);
    assert(apply_calls == 1 && q.orientation == REVERSE && q.qmpphy_mode == USB4);
    struct qmp_combo failed = {
        .cfg = &cfg, .vregs = bulk, .reset_pending = true,
        .orientation = REVERSE, .p2rr2p_pipe_clk = 1
    };
    struct phy phy = { .qmp = &failed };
    reset_error = -ETIMEDOUT;
    assert(qmp_combo_usb_init(&phy) == -EIO);
    assert(failed.init_count == 0 && failed.usb_init_count == 0);
    apply_calls = 0;
    assert(qmp_combo_usb4_init(&phy) == -EIO);
    assert(failed.init_count == 0 && failed.usb4_init_count == 0);
    return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix="a16-qmp-regression-") as tmp:
        source = Path(tmp) / "qmp.c"
        binary = Path(tmp) / "qmp"
        source.write_text(harness + helper + rollback +
                          function(qmp, "qmp_combo_usb_init") +
                          function(qmp, "qmp_combo_usb4_init") + cases)
        subprocess.run(shlex.split(os.environ.get("HOSTCC", "cc")) +
                       ["-std=c11", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print("PASS: compiled QMP reset/regulator failure retries, reference counts, failed USB/USB4 init and Type-C rollback")


if __name__ == "__main__":
    check(Path(sys.argv[1]))
