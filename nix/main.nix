let
  pydrive = pkgs: import ./pydrive.nix {inherit pkgs;};
  duplKey = builtins.readFile ../secrets/pydriveprivatekey.pem;
  dbPath = "/opt/gchatautorespond/gchatautorespond_db.sqlite3";
  # this includes the process output + systemd context (eg "starting foo..." messages)
  logUnitYaml = lib: builtins.toJSON (lib.lists.flatten (builtins.map (x: [ "UNIT=${x}" "_SYSTEMD_UNIT=${x}" ]) [
    "acme-gchat.simon.codes.service"
    "duplicity.service"
    "gchatautorespond-chatworker.service"
    "gchatautorespond-delete_old_emails.service"
    "gchatautorespond-reenable_bots.service"
    "gchatautorespond-sync_licenses.service"
    "gchatautorespond-testworker.service"
    "gchatautorespond-web.service"
    "nginx.service"
    "sshd.service"
  ]));
in let
  genericConf = { config, pkgs, lib, ... }: {
    services.nginx = {
      enable = true;
      recommendedGzipSettings = true;
      recommendedOptimisation = true;
      recommendedProxySettings = true;
      recommendedTlsSettings = true;
      upstreams.gunicorn = {
        servers = {
          "127.0.0.1:8000" = {};
        };
        # extraConfig = "fail_timeout=0";
      };
      virtualHosts."gchat.simon.codes" = {
        enableACME = true;
        forceSSL = true;
        locations."/assets/" = {
          alias = "/opt/gchatautorespond/assets/";
        };
        locations."/" = {
          proxyPass = "http://gunicorn";
        };
      };
      # reject requests with bad host headers
      virtualHosts."_" = {
        onlySSL = true;
        default = true;
        sslCertificate = ./fake-cert.pem;
        sslCertificateKey = ./fake-key.pem;
        extraConfig = "return 444;";
      };
      appendHttpConfig = ''
        error_log stderr;
        access_log syslog:server=unix:/dev/log combined;
      '';
    };
    services.journalbeat = {
      enable = true;
      extraConfig = ''
        journalbeat.inputs:
        - paths: ["/var/log/journal"]
          include_matches: ${(logUnitYaml lib)}
        output:
         elasticsearch:
           hosts: ["https://cloud.humio.com:443/api/v1/ingest/elastic-bulk"]
           username: anything
           password: ${builtins.readFile ../secrets/humiocloud.password}
           compression_level: 5
           bulk_max_size: 200
           worker: 1
           template.enabled: false
      '';
    };
    services.duplicity = {
      enable = true;
      root = "/tmp/db.backup";
      targetUrl = "pydrive://duply-alpha@repominder.iam.gserviceaccount.com/gchatautoresponder_backups/db1";
      secretFile = pkgs.writeText "dupl.env" ''
        GOOGLE_DRIVE_ACCOUNT_KEY="${duplKey}"
      '';
      extraFlags = ["--no-encryption"];
    };
    services.openssh = {
      enable = true;
    };

    systemd.services.duplicity = {
      path = [ pkgs.bash pkgs.sqlite ];
      preStart = ''sqlite3 ${dbPath} ".backup /tmp/db.backup"'';
      # privateTmp should handle this, but this helps in case it's eg disabled upstream
      postStop = "rm /tmp/db.backup";
    };
    systemd.services.gchatautorespond-web = {
      enable = true;
      description = "gchatautorespond web";
      after = [ "network-online.target" ];
      wantedBy = [ "network-online.target" ];
      path = [ pkgs.python27 pkgs.bash ];
      environment = {
        DJANGO_SETTINGS_MODULE = "gchatautorespond.settings";
      };
      serviceConfig = {
        WorkingDirectory = "/opt/gchatautorespond/code";
        ExecStart = "/opt/gchatautorespond/venv/exec gunicorn --worker-class gevent gchatautorespond.wsgi -b '127.0.0.1:8000'";
        Restart = "always";
        User = "gchatautorespond";
        Group = "gchatautorespond";
      };
    };
    systemd.services.gchatautorespond-chatworker = {
      enable = true;
      description = "gchatautorespond chatworker";
      after = [ "network-online.target" ];
      wantedBy = [ "network-online.target" ];
      path = [ pkgs.python27 pkgs.bash ];
      environment = {
        DJANGO_SETTINGS_MODULE = "gchatautorespond.settings";
      };
      serviceConfig = {
        WorkingDirectory = "/opt/gchatautorespond/code";
        ExecStart = "/opt/gchatautorespond/venv/exec python run_worker.py";
        Restart = "always";
        User = "gchatautorespond";
        Group = "gchatautorespond";
      };
    };
    systemd.services.gchatautorespond-testworker = {
      enable = true;
      description = "gchatautorespond testworker";
      after = [ "network-online.target" ];
      wantedBy = [ "network-online.target" ];
      path = [ pkgs.python27 pkgs.bash ];
      environment = {
        DJANGO_SETTINGS_MODULE = "gchatautorespond.settings";
      };
      serviceConfig = {
        WorkingDirectory = "/opt/gchatautorespond/code";
        ExecStart = "/opt/gchatautorespond/venv/exec python run_testworker.py";
        Restart = "always";
        User = "gchatautorespond";
        Group = "gchatautorespond";
      };
    };
    systemd.services.gchatautorespond-delete_old_emails = {
      enable = true;
      description = "gchatautorespond delete old emails";
      startAt = "daily";
      path = [ pkgs.python27 pkgs.bash ];
      environment = {
        DJANGO_SETTINGS_MODULE = "gchatautorespond.settings";
      };
      serviceConfig = {
        WorkingDirectory = "/opt/gchatautorespond/code";
        ExecStart = "/opt/gchatautorespond/venv/exec python delete_old_mail.py";
        User = "gchatautorespond";
        Group = "gchatautorespond";
      };
    };
    systemd.services.gchatautorespond-reenable_bots = {
      enable = true;
      description = "gchatautorespond reenable bots";
      startAt = "hourly";
      path = [ pkgs.python27 pkgs.bash ];
      environment = {
        DJANGO_SETTINGS_MODULE = "gchatautorespond.settings";
      };
      serviceConfig = {
        WorkingDirectory = "/opt/gchatautorespond/code";
        ExecStart = "/opt/gchatautorespond/venv/exec python reenable_bots.py";
        User = "gchatautorespond";
        Group = "gchatautorespond";
      };
    };
    systemd.services.gchatautorespond-sync_licenses = {
      enable = true;
      description = "gchatautorespond sync licenses";
      startAt = "*-*-* 11:00:00";  # mornings eastern
      path = [ pkgs.python27 pkgs.bash ];
      environment = {
        DJANGO_SETTINGS_MODULE = "gchatautorespond.settings";
      };
      serviceConfig = {
        WorkingDirectory = "/opt/gchatautorespond/code";
        ExecStart = "/opt/gchatautorespond/venv/exec python sync_licenses.py";
        User = "gchatautorespond";
        Group = "gchatautorespond";
      };
    };
    users = {
      # using another user for admin tasks would be preferable, but nixops requires root ssh anyway:
      # https://github.com/NixOS/nixops/issues/730
      users.root.openssh.authorizedKeys.keyFiles = [ ../../.ssh/id_rsa.pub ];
      users.gchatautorespond = {
        group = "gchatautorespond";
        isSystemUser = true;
      };
      groups.gchatautorespond.members = [ "gchatautorespond" "nginx" ];
    };

    networking.firewall.allowedTCPPorts = [ 22 80 443 ];

    nixpkgs.config = {
      allowUnfree = true;
    };
    nixpkgs.overlays = [ (self: super: {
      duplicity = super.duplicity.overrideAttrs (oldAttrs: { 
        propagatedBuildInputs = oldAttrs.propagatedBuildInputs ++ [ (pydrive pkgs).packages.PyDrive ];
        doCheck = false;
        doInstallCheck = false;
      });
    }
    )];

    environment.systemPackages = with pkgs; [
      git  # for vcs pip support
      sqlite
      duplicity
      vim
      (python27.withPackages(ps: with ps; [ virtualenv pip ]))
    ];
  };
in {
  network.description = "gchatautorespond";
  network.enableRollback = true;
  virtualbox = genericConf;
  bravo-simon-codes = genericConf;
}
