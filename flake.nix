{
  description = "PSF Viewer: a Streamlit app for visualizing PSF models from just-focus";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        python3 = pkgs.python3;

        # `zernipax` and `just-focus` aren't packaged in nixpkgs, so they're built
        # here directly from the wheels published on PyPI. Hashes were verified
        # against the sha256 values recorded in uv.lock.
        zernipax = python3.pkgs.buildPythonPackage {
          pname = "zernipax";
          version = "0.2.1";
          format = "wheel";
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/43/95/95798cfe41979ee71ce161734ef4a2a4894461b484332fd75d570076507d/zernipax-0.2.1-py3-none-any.whl";
            hash = "sha256-zkQURQT0KHfDh9rKTLlow3T346SZun9TbJEqOfdKYyA=";
          };
          propagatedBuildInputs = with python3.pkgs; [
            jax
            matplotlib
            mpmath
            numpy
          ];
          doCheck = false;
          pythonImportsCheck = [ "zernipax" ];
        };

        just-focus = python3.pkgs.buildPythonPackage {
          pname = "just_focus";
          version = "1.1.0";
          format = "wheel";
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/3a/a2/716b0b741c7fe7f79527868cc368ac7601ec744828a107670ce6a8cb9a29/just_focus-1.1.0-py3-none-any.whl";
            hash = "sha256-q6CgmWbSY1/q4VjfnjCBh+8efK0ctaqAnjKeR5FdQ+A=";
          };
          propagatedBuildInputs = [
            python3.pkgs.numpy
            zernipax
          ];
          doCheck = false;
          pythonImportsCheck = [ "leb.just_focus" ];
        };

        pythonEnv = python3.withPackages (
          ps: with ps; [
            streamlit
            matplotlib
            numpy
            just-focus
            zernipax
          ]
        );
      in
      {
        packages.default = pkgs.runCommand "psf-viewer" { nativeBuildInputs = [ pkgs.makeWrapper ]; } ''
          mkdir -p $out/share/psf-viewer $out/bin
          cp ${./app.py} $out/share/psf-viewer/app.py
          makeWrapper ${pythonEnv}/bin/streamlit $out/bin/psf-viewer \
            --add-flags "run $out/share/psf-viewer/app.py --server.headless true" \
            --set STREAMLIT_BROWSER_GATHER_USAGE_STATS false
        '';

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/psf-viewer";
        };

        devShells.default = pkgs.mkShell { packages = [ pythonEnv ]; };
      }
    )
    // {
      nixosModules.default = import ./nix/module.nix self;
    };
}
