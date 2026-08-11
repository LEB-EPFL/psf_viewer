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
