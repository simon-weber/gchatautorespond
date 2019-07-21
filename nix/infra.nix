{
  virtualbox =
    { config, pkgs, ... }:
    { deployment.targetEnv = "virtualbox";
      deployment.virtualbox.memorySize = 1024;
      deployment.virtualbox.vcpu = 2;
      deployment.virtualbox.headless = true;
      services.openssh = {
        # set in the GCE import
        permitRootLogin = "yes";
      };
    };
  bravo-simon-codes =
    { config, lib, pkgs, ... }:
    { deployment.targetHost = "bravo.simon.codes";
      imports = [ <nixpkgs/nixos/modules/virtualisation/google-compute-image.nix> ];
    };
}
