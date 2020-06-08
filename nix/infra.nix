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

  foxtrot-simon-codes =
    { config, lib, pkgs, ... }:
    { deployment.targetHost = "foxtrot.simon.codes";
      networking.hostName = "foxtrot";
      networking.domain = "simon.codes";
      services.openssh = {
        enable = true;
        passwordAuthentication = false;
        challengeResponseAuthentication = false;
        extraConfig = "AllowUsers root";
      };

      boot.loader.grub.device = "/dev/vda";

      boot.initrd.availableKernelModules = [ "ata_piix" "uhci_hcd" "virtio_pci" "sr_mod" "virtio_blk" ];
      boot.kernelModules = [ "kvm-amd" ];
      boot.extraModulePackages = [ ];

      fileSystems."/" =
        { device = "/dev/disk/by-uuid/ed9701b4-5616-4118-a579-98bf622558e2";
        fsType = "ext4";
      };

      swapDevices =
        [ { device = "/dev/disk/by-uuid/7c154511-8ead-4ce6-8692-d08a315d0697"; }
      ];

      nix.maxJobs = lib.mkDefault 1;
      virtualisation.hypervGuest.enable = false;
    };
}
