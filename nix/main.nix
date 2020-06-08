let
  duplKey = builtins.readFile ../secrets/pydriveprivatekey.pem;
  dbPath = "/opt/gchatautorespond/gchatautorespond_db.sqlite3";
  # this includes the process output + systemd context (eg "starting foo..." messages)
  logUnitYaml = lib: builtins.toJSON (lib.lists.flatten (builtins.map (x: [ "UNIT=${x}" "_SYSTEMD_UNIT=${x}" ]) [
    "acme-gchat.simon.codes.service"
    "duplicity.service"
    "docker.service"
    "docker-gchatautorespond-chatworker.service"
    "docker-gchatautorespond-delete_old_emails.service"
    "docker-gchatautorespond-reenable_bots.service"
    "docker-gchatautorespond-sync_licenses.service"
    "docker-gchatautorespond-testworker.service"
    "docker-gchatautorespond-web.service"
    "nginx.service"
    "sshd.service"
  ]));
in let
  genericConf = { config, pkgs, lib, ... }: {

    virtualisation.docker = {
      enable = true;
      logDriver = "journald";
    };
    docker-containers.gchatautorespond-web = {
      image = "gchatautorespond:latest";
      volumes = [ "/opt/gchatautorespond:/opt/gchatautorespond" ];
      extraDockerOptions = ["--network=host"];
    };

    docker-containers.gchatautorespond-chatworker = {
      image = "gchatautorespond:latest";
      volumes = [ "/opt/gchatautorespond:/opt/gchatautorespond" ];
      extraDockerOptions = ["--network=host"];
      entrypoint = "python";
      cmd = [ "run_worker.py" ];
    };

    docker-containers.gchatautorespond-testworker = {
      image = "gchatautorespond:latest";
      volumes = [ "/opt/gchatautorespond:/opt/gchatautorespond" ];
      extraDockerOptions = ["--network=host"];
      entrypoint = "python";
      cmd = [ "run_testworker.py" ];
    };

    docker-containers.gchatautorespond-delete_old_mails = {
      image = "gchatautorespond:latest";
      volumes = [ "/opt/gchatautorespond:/opt/gchatautorespond" ];
      extraDockerOptions = ["--network=host"];
      entrypoint = "python";
      cmd = [ "delete_old_mail.py" ];
    };
    systemd.services.docker-gchatautorespond-delete_old_mails = {
      startAt = "*-*-* 07:30:00";  # early mornings eastern
      wantedBy = pkgs.lib.mkForce [];
      serviceConfig = {
        Restart = pkgs.lib.mkForce "no";
        # TODO figure out how to merge these automatically
        # https://github.com/NixOS/nixpkgs/issues/76620
        ExecStopPost = pkgs.lib.mkForce [ "-${pkgs.docker}/bin/docker rm -f %n" "${pkgs.sqlite}/bin/sqlite3 ${dbPath} 'VACUUM;'" ];
      };
    };

    docker-containers.gchatautorespond-reenable_bots = {
      image = "gchatautorespond:latest";
      volumes = [ "/opt/gchatautorespond:/opt/gchatautorespond" ];
      extraDockerOptions = ["--network=host"];
      entrypoint = "python";
      cmd = [ "reenable_bots.py" ];
    };
    systemd.services.docker-gchatautorespond-reenable_bots = {
      startAt = "hourly";
      wantedBy = pkgs.lib.mkForce [];
      serviceConfig = {
        Restart = pkgs.lib.mkForce "no";
      };
    };

    docker-containers.gchatautorespond-sync_licenses = {
      image = "gchatautorespond:latest";
      volumes = [ "/opt/gchatautorespond:/opt/gchatautorespond" ];
      extraDockerOptions = ["--network=host"];
      entrypoint = "python";
      cmd = [ "sync_licenses.py" ];
    };
    systemd.services.docker-gchatautorespond-sync_licenses = {
      startAt = "*-*-* 11:30:00";  # mornings eastern
      wantedBy = pkgs.lib.mkForce [];
      serviceConfig = {
        # The process usually finishes on its own.
        # This makes it easier to set logging alerts for actually failing runs.
        ExecStop = pkgs.lib.mkForce "-${pkgs.docker}/bin/docker stop %n";
        Restart = pkgs.lib.mkForce "no";
      };
    };

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
      frequency = "*-*-* 00,12:30:00";
      root = "/tmp/db.backup";
      targetUrl = "pydrive://duply-alpha@repominder.iam.gserviceaccount.com/gchatautoresponder_backups/db3";
      secretFile = pkgs.writeText "dupl.env" ''
        GOOGLE_DRIVE_ACCOUNT_KEY="${duplKey}"
      '';
      extraFlags = ["--no-encryption" "--allow-source-mismatch"];
    };
    systemd.services.duplicity = {
      path = [ pkgs.bash pkgs.sqlite ];
      preStart = ''sqlite3 ${dbPath} ".backup /tmp/db.backup"'';
      # privateTmp should handle this, but this helps in case it's eg disabled upstream
      postStop = "rm /tmp/db.backup";
    };

    users = {
      # using another user for admin tasks would be preferable, but nixops requires root ssh anyway:
      # https://github.com/NixOS/nixops/issues/730
      users.root.extraGroups = [ "docker" ];
      users.root.openssh.authorizedKeys.keyFiles = [ ../../.ssh/id_rsa.pub ];
      users.gchatautorespond = {
        group = "gchatautorespond";
        isSystemUser = true;
        uid = 497;
      };
      groups.gchatautorespond = {
        members = [ "gchatautorespond" "nginx" ];
        gid = 499;
      };
    };

    networking.firewall.allowedTCPPorts = [ 22 80 443 ];

    security.acme.acceptTerms = true;
    security.acme.email = "domains@simonmweber.com";

    nixpkgs.config = {
      allowUnfree = true;
    };
    nixpkgs.overlays = [ (self: super: {
      duplicity = super.duplicity.overrideAttrs (oldAttrs: { 
        doCheck = false;
        doInstallCheck = false;
      });
    }
    )];

    environment.systemPackages = with pkgs; [
      curl
      sqlite
      duplicity
      htop
      iotop
      sysstat
      vim
      python3  # for ansible
    ];
  };
in {
  network.description = "gchatautorespond";
  network.enableRollback = true;
  virtualbox = genericConf;
  foxtrot-simon-codes = genericConf;
}
