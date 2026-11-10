# Root cause: GNOME login fails under /proc hidepid

**Problem.** On CloudLinux 9 with a desktop installed, users could not log in to GNOME. CloudLinux mounts `/proc` with `hidepid` to isolate users from each other, and that isolation had to stay.

**What I did.** I traced the failure from the login screen down to a library call, compared it with newer systems and prepared a minimal fix that keeps isolation intact. I verified it on test VMs, with a control run without the fix.

## The chain I traced

```mermaid
flowchart TB
    H["/proc mounted with hidepid"] --> S["libsystemd sd_pid_get_session() cannot read /proc/1/cgroup and returns ESRCH"]
    S --> M40["mutter 40 on CloudLinux 9 treats ESRCH as fatal: 'Could not get session ID'"]
    S --> M48["mutter 48+ uses logind over D-Bus and falls back on errors"]
    M40 --> F["GNOME Wayland session does not start"]
    M48 --> OK["Login works"]
    F --> Fix["Fix: gdm drop-in that disables Wayland only when hidepid is active and the admin has not chosen otherwise"]
    Fix --> X11["X11 GNOME session works, isolation stays"]
```

Public references: [systemd issue #12955](https://github.com/systemd/systemd/issues/12955), [mutter merge request 4022](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/4022).

**Stack:** systemd, GDM, mutter, Linux /proc, test VMs.
