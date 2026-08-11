self:
{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.psf-viewer;
in
{
  options.services.psf-viewer = {
    enable = mkEnableOption "PSF Viewer, a Streamlit app for visualizing PSF models";

    package = mkOption {
      type = types.package;
      default = self.packages.${pkgs.system}.default;
      description = "The psf-viewer package to run.";
    };

    address = mkOption {
      type = types.str;
      default = "0.0.0.0";
      description = "Address the Streamlit server binds to.";
    };

    port = mkOption {
      type = types.port;
      default = 8501;
      description = "Port the app is served on.";
    };

    openFirewall = mkOption {
      type = types.bool;
      default = false;
      description = "Whether to open the configured port in the firewall.";
    };
  };

  config = mkIf cfg.enable {
    systemd.services.psf-viewer = {
      description = "PSF Viewer";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];

      environment = {
        STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false";
      };

      serviceConfig = {
        ExecStart = "${cfg.package}/bin/psf-viewer --server.address=${cfg.address} --server.port=${toString cfg.port}";
        Restart = "on-failure";
        RestartSec = 5;

        DynamicUser = true;
        NoNewPrivileges = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        PrivateTmp = true;
      };
    };

    networking.firewall.allowedTCPPorts = mkIf cfg.openFirewall [ cfg.port ];
  };
}
