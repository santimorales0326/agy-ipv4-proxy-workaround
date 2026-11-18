#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v python3 >/dev/null || { echo 'Python 3 required' >&2; exit 1; }
command -v systemctl >/dev/null || { echo 'systemd user services required' >&2; exit 1; }
AGY_PATH="$(type -P agy || true)"
if [[ -z "$AGY_PATH" ]]; then
  echo 'agy executable not found in PATH; install agy first.' >&2
  exit 1
fi
mkdir -p "$HOME/.local/share/agy-ipv4-proxy" "$HOME/.config/systemd/user" "$HOME/.local/bin"
install -m 0644 "$ROOT/proxy.py" "$HOME/.local/share/agy-ipv4-proxy/proxy.py"
install -m 0644 "$ROOT/systemd/agy-ipv4-proxy.service" "$HOME/.config/systemd/user/agy-ipv4-proxy.service"
cat > "$HOME/.local/bin/agy4" <<WRAPPER
#!/usr/bin/env bash
export HTTPS_PROXY=http://127.0.0.1:18888
export HTTP_PROXY=http://127.0.0.1:18888
export ALL_PROXY=http://127.0.0.1:18888
export NO_PROXY=
export no_proxy=
exec "$AGY_PATH" "\$@"
WRAPPER
chmod 0755 "$HOME/.local/bin/agy4"
systemctl --user daemon-reload
systemctl --user enable --now agy-ipv4-proxy.service
cat <<'MSG'
Installed. Test: curl -x http://127.0.0.1:18888 https://api.ipify.org
Run: ~/.local/bin/agy4
To use 'agy' in Bash, add to ~/.bashrc:
  agy() { "$HOME/.local/bin/agy4" "$@"; }
Then run: source ~/.bashrc
MSG
