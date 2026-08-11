# PSF Viewer

A Streamlit app for interactively visualizing point spread function (PSF) models
from the `just-focus` library in a high-NA microscope objective.

Choose a pupil model (Gaussian or Halfmoon), polarization state, and aberrations,
and see how the pupil-plane amplitude, phase, and polarization maps translate into
the focal-plane irradiance at `z = 0`.

## Features

- **PSF models**: Gaussian or Halfmoon (Gaussian amplitude with a half-wave phase
  step)
- **Polarization**: linear X, linear Y, circular left, circular right
- **Halfmoon orientation**: horizontal, vertical, +45°, -45°, with an adjustable
  phase step
- **Beam parameters**: pupil center and waist
- **Optics**: numerical aperture, wavelength, refractive index, focal length
- **Numerical settings**: mesh size, stop type (uniform/tanh) and radius, FFT
  padding factor, field of view
- **Zernike aberrations**: sliders for Noll indices 1-11 (piston through primary
  spherical)

The main view shows amplitude, phase, and stop in the pupil plane; polarization in
x and y; and the irradiance in the focal plane at `z = 0`.

## Setup

Requires Python 3.14+ and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Running locally

```bash
uv run streamlit run app.py
```

This serves the app on `http://localhost:8501`, accessible only from this machine.

## Serving on your local network

To let other devices on your network (a few concurrent users) reach the app, bind
to all interfaces:

```bash
uv run streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

Streamlit prints both a local URL and a "Network URL" — share the Network URL
(`http://<your-lan-ip>:8501`) with other users on the same network. There's no
authentication, so only run this on a trusted network.

To stop the server, press `Ctrl-C` in the terminal it's running in, or from
another terminal:

```bash
lsof -ti:8501 -sTCP:LISTEN | xargs kill
```

## Running as a systemd service on NixOS

`flake.nix` packages the app with pure Nix (no `uv` involved) and provides a
NixOS module that runs it as a systemd service. `just-focus` and `zernipax`
aren't in nixpkgs, so the flake builds them directly from their published PyPI
wheels; everything else (`streamlit`, `matplotlib`, `numpy`, `jax`, ...) comes
from nixpkgs.

Add the flake as an input and enable the module in your system configuration:

```nix
{
  inputs.psf-viewer.url = "github:<your-username>/psf-viewer"; # or "path:/path/to/psf_viewer"

  outputs = { self, nixpkgs, psf-viewer, ... }: {
    nixosConfigurations.<hostname> = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        psf-viewer.nixosModules.default
        {
          services.psf-viewer = {
            enable = true;
            port = 8501;          # default
            address = "0.0.0.0";  # default; binds to all interfaces for LAN access
            openFirewall = true;  # opens `port` in the NixOS firewall
          };
        }
        # ...your other modules
      ];
    };
  };
}
```

Then rebuild:

```bash
sudo nixos-rebuild switch --flake .#<hostname>
```

The service runs under a `DynamicUser`, restarts on failure, and is reachable
at `http://<server-ip>:8501` from any device on the LAN. Check its status
with `systemctl status psf-viewer` and logs with `journalctl -u psf-viewer -f`.

You can also build and run the package directly without a full NixOS module,
e.g. for a quick manual test:

```bash
nix run .#default -- --server.address=0.0.0.0 --server.port=8501
```

Note: since this is a flake, any file it needs (`app.py`, `nix/module.nix`)
must be tracked by `git` (at least `git add`ed) for Nix to see it.
