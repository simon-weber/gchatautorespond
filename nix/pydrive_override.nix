{ pkgs, python }:

self: super: {
  "six" = pkgs.python27Packages.six;
  "pyasn1" = pkgs.python27Packages.pyasn1;
}
