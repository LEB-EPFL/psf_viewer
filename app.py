"""Streamlit app for visualizing point spread function (PSF) models.

Run with:

    uv run streamlit run app.py --server.address=0.0.0.0

"""

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from leb.just_focus import HalfmoonPhase, InputField, Polarization, Pupil, Stop
from leb.just_focus.zernike import zernike_pupil_coordinates

NOLL_NAMES = {
    1: "Piston",
    2: "Tip (X tilt)",
    3: "Tilt (Y tilt)",
    4: "Defocus",
    5: "Oblique astigmatism",
    6: "Vertical astigmatism",
    7: "Vertical coma",
    8: "Horizontal coma",
    9: "Vertical trefoil",
    10: "Oblique trefoil",
    11: "Primary spherical",
}
NOLL_INDICES = list(NOLL_NAMES.keys())

POLARIZATION_LABELS = {
    Polarization.LINEAR_X: "Linear, X",
    Polarization.LINEAR_Y: "Linear, Y",
    Polarization.CIRCULAR_LEFT: "Circular, left",
    Polarization.CIRCULAR_RIGHT: "Circular, right",
}

HALFMOON_LABELS = {
    HalfmoonPhase.HORIZONTAL: "Horizontal",
    HalfmoonPhase.VERTICAL: "Vertical",
    HalfmoonPhase.PLUS_45: "+45°",
    HalfmoonPhase.MINUS_45: "-45°",
}

STOP_LABELS = {
    Stop.TANH: "Tanh (smoothed edge)",
    Stop.UNIFORM: "Uniform (hard edge)",
}


@st.cache_data(show_spinner="Computing focal field...")
def compute(
    model: str,
    polarization: str,
    orientation: str,
    halfmoon_phase: float,
    beam_center_x: float,
    beam_center_y: float,
    waist: float,
    na: float,
    wavelength_um: float,
    refractive_index: float,
    focal_length_mm: float,
    mesh_size: int,
    stop_type: str,
    stop_radius_pupil: float,
    padding_factor: int,
    zernike_coefficients: tuple[float, ...],
):
    """Build the pupil and input fields, then propagate to the z = 0 focal plane."""
    pupil = Pupil(
        na=na,
        wavelength_um=wavelength_um,
        refractive_index=refractive_index,
        focal_length_mm=focal_length_mm,
        mesh_size=mesh_size,
        stop=Stop(stop_type),
        stop_radius_pupil=stop_radius_pupil,
    )

    pol = Polarization(polarization)
    if model == "Gaussian":
        inputs = InputField.gaussian_pupil(
            beam_center_pupil=(beam_center_x, beam_center_y),
            waist_pupil=waist,
            mesh_size=mesh_size,
            polarization=pol,
        )
    else:
        inputs = InputField.gaussian_halfmoon_pupil(
            beam_center_pupil=(beam_center_x, beam_center_y),
            waist_pupil=waist,
            mesh_size=mesh_size,
            polarization=pol,
            orientation=HalfmoonPhase(orientation),
            phase=halfmoon_phase,
            phase_mask_center=(0.0, 0.0),
        )

    if any(c != 0.0 for c in zernike_coefficients):
        inputs = inputs.with_zernike_modes(NOLL_INDICES, list(zernike_coefficients))

    results = pupil.propgate(0.0, inputs, padding_factor=padding_factor)
    return pupil, inputs, results


def pupil_panel(
    data: np.ndarray,
    pupil: Pupil,
    title: str,
    vmin: float | None,
    vmax: float | None,
    cmap: str,
) -> Figure:
    fig, ax = plt.subplots(figsize=(3.6, 3.2))
    im = ax.imshow(
        data,
        vmin=vmin,
        vmax=vmax,
        cmap=cmap,
        origin="lower",
        extent=(pupil.x_mm[0], pupil.x_mm[-1], pupil.y_mm[0], pupil.y_mm[-1]),
    )
    ax.add_artist(
        Circle((0, 0), radius=pupil.stop_radius_mm, color="k", fill=False, linewidth=1.5)
    )
    ax.set_title(title)
    ax.set_xlabel("x, mm")
    ax.set_ylabel("y, mm")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    return fig


def irradiance_panel(results, half_fov_um: float) -> Figure:
    fig, ax = plt.subplots(figsize=(3.6, 3.2))
    im = ax.imshow(
        results.intensity(normalize=True),
        vmin=0,
        vmax=1,
        cmap="inferno",
        origin="lower",
        extent=(results.x_um[0], results.x_um[-1], results.y_um[0], results.y_um[-1]),
    )
    ax.set_title("Irradiance, z = 0")
    ax.set_xlabel(r"x, $\mu m$")
    ax.set_ylabel(r"y, $\mu m$")
    ax.set_xlim(-half_fov_um, half_fov_um)
    ax.set_ylim(-half_fov_um, half_fov_um)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    return fig


st.set_page_config(page_title="PSF Viewer", layout="wide")
st.title("PSF Viewer")

with st.sidebar:
    st.header("Model")
    model = st.radio("PSF model", ["Gaussian", "Halfmoon"], horizontal=True)
    polarization = st.selectbox(
        "Polarization",
        list(POLARIZATION_LABELS.keys()),
        format_func=lambda p: POLARIZATION_LABELS[p],
    )

    orientation = HalfmoonPhase.HORIZONTAL
    halfmoon_phase_pi = 1.0
    if model == "Halfmoon":
        st.header("Halfmoon")
        orientation = st.selectbox(
            "Orientation",
            list(HALFMOON_LABELS.keys()),
            format_func=lambda o: HALFMOON_LABELS[o],
        )
        halfmoon_phase_pi = st.slider(
            "Phase step, ×π rad", 0.0, 2.0, 1.0, 0.05
        )

    with st.expander("Beam", expanded=True):
        beam_center_x = st.slider("Beam center, x (pupil)", -1.0, 1.0, 0.0, 0.05)
        beam_center_y = st.slider("Beam center, y (pupil)", -1.0, 1.0, 0.0, 0.05)
        waist = st.slider("Waist (pupil)", 0.1, 3.0, 1.0, 0.1)

    with st.expander("Optics"):
        na = st.slider("Numerical aperture", 0.1, 1.49, 1.4, 0.01)
        wavelength_um = st.slider("Wavelength, µm", 0.4, 0.7, 0.532, 0.001)
        refractive_index = st.slider("Refractive index", 1.0, 1.6, 1.518, 0.001)
        focal_length_mm = st.number_input("Focal length, mm", 0.1, 20.0, 3.3333)

    with st.expander("Numerical settings"):
        mesh_size = st.select_slider("Mesh size", [32, 64, 128, 256], value=64)
        stop_type = st.selectbox(
            "Stop", list(STOP_LABELS.keys()), format_func=lambda s: STOP_LABELS[s], index=0
        )
        stop_radius_pupil = st.slider("Stop radius (pupil)", 0.1, 1.0, 1.0, 0.01)
        padding_factor = st.slider(
            "Padding factor", 1, 4, 3, help="Higher values increase image resolution but are slower to compute."
        )
        half_fov_um = st.slider("Half field of view, µm", 0.2, 5.0, 1.0, 0.1)

    with st.expander("Zernike aberrations (Noll 1–11)"):
        if st.button("Reset to zero"):
            for j in NOLL_INDICES:
                st.session_state[f"noll_{j}"] = 0.0
        zernike_coefficients = tuple(
            st.slider(f"Z{j}: {NOLL_NAMES[j]}", -3.0, 3.0, 0.0, 0.05, key=f"noll_{j}")
            for j in NOLL_INDICES
        )

pupil, inputs, results = compute(
    model=model,
    polarization=polarization.value,
    orientation=orientation.value,
    halfmoon_phase=halfmoon_phase_pi * np.pi,
    beam_center_x=beam_center_x,
    beam_center_y=beam_center_y,
    waist=waist,
    na=na,
    wavelength_um=wavelength_um,
    refractive_index=refractive_index,
    focal_length_mm=focal_length_mm,
    mesh_size=mesh_size,
    stop_type=stop_type.value,
    stop_radius_pupil=stop_radius_pupil,
    padding_factor=padding_factor,
    zernike_coefficients=zernike_coefficients,
)

# Zernike polynomials (and therefore the aberrated phase) are only defined on the
# unit disk, so mask out everything beyond the stop before displaying pupil-plane maps.
rho, _ = zernike_pupil_coordinates(mesh_size)
pupil_mask = rho <= pupil.stop_radius_pupil

amplitude_x = np.where(pupil_mask, inputs.amplitude_x, np.nan)
phase_x = np.where(pupil_mask, np.angle(np.exp(1j * inputs.phase_x)), np.nan)
polarization_x = np.where(pupil_mask, np.abs(inputs.polarization_x), np.nan)
polarization_y = np.where(pupil_mask, np.abs(inputs.polarization_y), np.nan)

def show(column, fig: Figure) -> None:
    with column:
        st.pyplot(fig)
    plt.close(fig)


row1 = st.columns(3)
show(row1[0], pupil_panel(amplitude_x, pupil, "Amplitude", 0, 1, "viridis"))
show(row1[1], pupil_panel(phase_x, pupil, "Phase", -np.pi, np.pi, "twilight"))
show(row1[2], pupil_panel(pupil.stop_arr, pupil, "Stop", 0, 1, "gray"))

row2 = st.columns(3)
show(row2[0], pupil_panel(polarization_x, pupil, "Polarization, x", 0, 1, "viridis"))
show(row2[1], pupil_panel(polarization_y, pupil, "Polarization, y", 0, 1, "viridis"))
show(row2[2], irradiance_panel(results, half_fov_um))
