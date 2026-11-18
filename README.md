# agy IPv4 proxy workaround

A localhost-only IPv4 HTTPS CONNECT proxy for the `agy` CLI on Linux VPS hosts.

On an OVHcloud VPS in Paris, `agy` v1.5.10 failed with:

```text
FAILED_PRECONDITION (code 400): User location is not supported for the API use.
```

The same client worked when routed through an IPv4-only localhost proxy, and failed again without it. This supports an IPv6-path-related issue, **not a definitive diagnosis** of Google's location checks.

## Requirements

Linux, Python 3, systemd user services, `agy` installed in `PATH`, and working IPv4 connectivity.

## Installation

Review the scripts first:

```bash
git clone https://github.com/santimorales0326/agy-ipv4-proxy-workaround.git
cd agy-ipv4-proxy-workaround
bash install.sh
```

The installer places `proxy.py` in `~/.local/share/agy-ipv4-proxy`, installs a systemd **user** service, and creates `~/.local/bin/agy4`. It does not disable IPv6 or modify host networking.

## Verify and use

```bash
systemctl --user is-active agy-ipv4-proxy.service
curl -sS -x http://127.0.0.1:18888 https://api.ipify.org
~/.local/bin/agy4
```

To keep typing `agy` in interactive Bash, append to `~/.bashrc`:

```bash
agy() { "$HOME/.local/bin/agy4" "$@"; }
```

Then run `source ~/.bashrc`.

## Troubleshooting

If systemd reports `activating`, check for a port conflict: the original manually launched proxy might still be listening.

```bash
journalctl --user -u agy-ipv4-proxy.service -n 30 --no-pager
sudo ss -ltnp 'sport = :18888'
```

Stop the manually started proxy (Ctrl+C in its terminal) and restart:

```bash
systemctl --user restart agy-ipv4-proxy.service
```

For services to survive logout, your system may require `sudo loginctl enable-linger "$USER"`. Only enable this if appropriate.

## How it works

The proxy listens only on `127.0.0.1:18888`, accepts HTTPS CONNECT requests to port 443, and opens upstream sockets via IPv4 (`AF_INET`). It forwards encrypted TLS traffic without decrypting it. The wrapper configures `HTTPS_PROXY`, `HTTP_PROXY`, and `ALL_PROXY` for `agy`.

## Security and limitations

- **Do not expose the proxy publicly.** No authentication, rate limiting, or host allowlist is provided; other local users might reach the listener.
- The proxy can see target hostnames, though it does not decrypt TLS.
- Applications may bypass proxy environment variables for some connections.
- This does not change the VPS country or guarantee Gemini eligibility.
- This is a small community workaround, **not a production-hardened proxy**.

## Tests

```bash
python3 -m unittest discover -s tests -v
bash -n install.sh
```

## Uninstall

```bash
systemctl --user disable --now agy-ipv4-proxy.service
rm -f ~/.config/systemd/user/agy-ipv4-proxy.service ~/.local/bin/agy4
rm -rf ~/.local/share/agy-ipv4-proxy
systemctl --user daemon-reload
```

Remove the optional `agy()` function from `~/.bashrc`.

## Background

[Original detailed Blogger troubleshooting post](https://santimorales0326.blogspot.com/2026/11/fixed-gemini-location-not-supported-on.html).

## Contributions

Issues and pull requests are welcome. Redact tokens, credentials, and full public IP addresses.

## License

MIT. See [LICENSE](LICENSE).
