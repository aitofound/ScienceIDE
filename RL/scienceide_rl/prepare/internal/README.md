# Internal appendix: one cluster's node provisioning

**These scripts encode the setup of the specific cluster this recipe was developed
on. They are published as a reference, not as a supported part of the recipe.**
Nothing under `scienceide_rl/` outside this directory calls them.

They hardcode, or default to, site-specific values: a Tencent Cloud container
registry mirror, a Debian apt mirror, an internal HTTP proxy, and a
`172.16.0.0/12` address pool for the Docker bridge. On any other cluster those
values are wrong, and `start_distributed_training.sh` additionally assumes a
3-node by 8-GPU layout read from a hostfile.

| File | What it does |
|------|--------------|
| `provision_docker_nodes.sh` | Configures dockerd registry mirrors and a buildkit proxy on a list of hosts. `--check` is read-only and exits 3 if any host needs work. |
| `NEW_NODE_RUNBOOK.md` | The procedure that was actually followed to bring five fresh nodes online, with the failure modes hit along the way. |
| `start_distributed_training.sh` | Preflights a 3-node cluster (free GPUs, reachable hosts, healthy Docker) before launching training. |

## What is worth reading here even on a different cluster

The knowledge, rather than the values:

- **Buildkit does not inherit the shell's proxy.** `dockerd` ignores user-space
  `http_proxy`, and buildkit needs its own client config. Image builds otherwise
  fail at `apt-get update` with no useful diagnostic.
- **A degraded Docker daemon does not announce itself.** It accepts work and then
  hangs every build. `timeout 20 docker ps -q` is the cheap probe, and
  `ps -eo comm | grep -c fuse-overlayfs` catches orphaned mounts.
- **Registry mirrors need a dockerd reload**, not just a config edit, or
  no-network tasks die at trial init.

## If you are adapting these

Override every site value explicitly rather than editing the defaults in place:

```bash
bash provision_docker_nodes.sh --hosts /path/to/hostfile --check \
    --proxy http://your-proxy-host:3128
```

The `--proxy`, `--registry-mirror`, and `--apt-mirror` flags exist for exactly
this. Run with `--check` first: it changes nothing and tells you what it would do.
