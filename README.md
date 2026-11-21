# Linux Alternate-View Forensics Suite: sample memory images

Memory images, Volatility 3 symbol tables (ISFs) and ground-truth manifests for the Linux Alternate-View
Forensics Suite (`linux.cgroupxview`, `linux.containerxview`, `linux.execxview`, `linux.iouringfiles`),
a Volatility Plugin Contest 2026 entry.

All images are x86-64 QEMU guests built in a lab. They contain only test workloads: no real user data
and no real malware. The three scenario images are copies of a benign capture with a few bytes edited
offline, and each one comes with a log of every edit.

## Layout

This repository has the same layout as the `lab-artifacts/` directory used in the suite's documentation
(`reproduce.md`, the judge quick-start in `README.md`, `expected_outputs/COMMANDS.md`), so every command
there works with `L=<path to this clone>`.

| Path | What |
|---|---|
| `symbols-<kver>/*.json.xz` | ISFs; pass the directory with `-s` |
| `vm-<kver>/dumps/<image>.manifests/` | ground truth recorded inside the guest at capture time (pids, cgroups, containers, io_uring cases, exec fixtures) |
| `vm-<kver>/dumps/<image>.pslist.txt`, `.kerneloffset.txt` | `linux.pslist` output and KASLR offset recorded at capture time |
| `vm-<kver>/*.boot-checks.txt` | guest checks run before each capture |
| `vm-6.6/scenarios/` | logs of the offline edits that produced the scenario images |
| `images.tsv` | each image: release asset, path, sha256 of the `.xz`, size, sha256 of the `.elf` |
| `fetch.py` | downloads, verifies and decompresses the images into this layout |

The images (`.elf`, 2,164,461,275 bytes each, 16 in total; 61 to 181 MB each compressed, 1.6 GB in all) are attached to the
[v1.0 release](https://github.com/danitzhaki/linux-altview-samples/releases/tag/v1.0) as `.elf.xz` files.

## Get the images

    git clone https://github.com/danitzhaki/linux-altview-samples
    cd linux-altview-samples
    python3 fetch.py --list                                   # what is available
    python3 fetch.py --only 6.6.162 --only 7.2.12-containers  # or no option for all 16

`fetch.py` needs only the Python standard library. It checks the sha256 of each download and of each
decompressed image. To do it by hand, download the `.xz` from the release page, run `xz -d`, and compare
with `sha256sum -c SHA256SUMS` (decompressed images) or `SHA256SUMS.xz` (release assets). `SHA256SUMS.isf` covers the ISFs.

## Images

| Image | Kernel and contents | ISF directory |
|---|---|---|
| `vm-6.6/dumps/deb12-6.6.162-default.elf` | 6.6.162 (self-built, PTI off): cgroup, exec, io_uring and zombie fixtures | `symbols-6.6` (`-lab`) |
| `vm-6.6/dumps/deb12-6.6.162-pti-on.elf` | the same kernel and fixtures, PTI on | `symbols-6.6` |
| `vm-6.6/dumps/deb12-6.6.162-containers.elf` | 6.6.162-labc: docker and podman containers | `symbols-6.6` (`-labc`) |
| `vm-6.6/dumps/deb12-6.6.162-container-escape.elf` | 6.6.162-labc: containers plus the escape-shape set | `symbols-6.6` |
| `vm-5.15/dumps/deb12-5.15.225-default.elf` | 5.15.225 (self-built, PTI off) | `symbols-5.15` |
| `vm-5.15/dumps/deb12-5.15.225-pti-on.elf` | 5.15.225, PTI on | `symbols-5.15` |
| `vm-6.1/dumps/deb12-6.1.190-default.elf` | Debian 12 stock 6.1.0-54 (6.1.190-1) | `symbols-6.1` |
| `vm-6.12/dumps/deb12-6.12.115-default.elf` | Debian 13 stock 6.12.115+deb13.1 (see the note below) | `symbols-6.12` |
| `vm-6.12/dumps/deb13-6.12.115-containers.elf` | Debian 13 6.12.115: containers | `symbols-6.12` |
| `vm-6.12/dumps/deb13-6.12.115-container-escape.elf` | Debian 13 6.12.115: containers plus the escape-shape set | `symbols-6.12` |
| `vm-7.2/dumps/deb13-7.2.12-default.elf` | Debian 13 with the trixie-backports kernel 7.2.12+deb13 | `symbols-7.2` |
| `vm-7.2/dumps/deb13-7.2.12-containers.elf` | 7.2.12: containers | `symbols-7.2` |
| `vm-7.2/dumps/deb13-7.2.12-container-escape.elf` | 7.2.12: containers plus the escape-shape set | `symbols-7.2` |
| `vm-6.6/scenarios/r2_exec_hide_vma.elf` | scenario: the 6.6 default image with one maple-tree slot set to NULL (8 bytes), hiding the VMA of pid 622 | `symbols-6.6` |
| `vm-6.6/scenarios/r2/cgroup_unlink_task.elf` | scenario: the 6.6 default image with pid 741 unlinked from its css_set task list (16 bytes) | `symbols-6.6` |
| `vm-6.6/scenarios/r2/cgroup_unlink_hierarchy.elf` | scenario: the 6.6 default image with the leaf cgroup `/altview/a/a1` unlinked from its parent's children list (16 bytes) | `symbols-6.6` |

The 6.12 default image keeps the file name `deb12-6.12.115-default.elf` because its hash was recorded
under that name; the guest is Debian 13 (trixie).

The 5.15 directory also holds `linux-5.15.225-labc.json.xz`, the ISF of the 5.15 container kernel. It
was built, but no container image was captured on 5.15.

The escape-shape set uses standard tools only, no exploit: `nsenter` from a privileged container, a
process whose cwd is in the host mount namespace, a host process written into a container cgroup, and
a container's only process moved to a host cgroup.

## Quick check

With the suite installed (see its `README.md`), from the Volatility 3 directory:

    L=/path/to/linux-altview-samples
    python vol.py -q -s $L/symbols-6.6 -f $L/vm-6.6/scenarios/r2/cgroup_unlink_task.elf linux.cgroupxview --mismatches-only

This prints one row: pid 741 `av_sl_b2`, `/altview/b`, `Missing` = `R`, `TASK_MEMBERSHIP_MISMATCH`. The same
command on `vm-6.6/dumps/deb12-6.6.162-default.elf` prints 0 rows.

## How the images were made

The guests are QEMU x86-64 VMs (TCG on an arm64 macOS host). Each image was captured with QEMU's
`dump-guest-memory` (ELF core) after the workloads reported ready. The build, capture and ISF steps are in
the suite's `reproduce.md` and `lab/` directory. The ISFs were generated with dwarf2json from the Debian
`-dbg` packages (stock kernels) or from the self-built kernels. The 7.2 ISF uses the DWARF `vmlinux` alone,
because Debian ships no `System.map` for that backport kernel.
