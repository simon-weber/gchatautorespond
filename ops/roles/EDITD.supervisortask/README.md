# ansible-supervisor_task

A role for creating supervisor tasks.


## Actions

- Ensures that supervisor is installed (using `apt`)
- Creates a task in the supervisor conf directory.


## Usage:
```
  roles:
    - role: EDITD.supervisor_task
      name: webserver
      command: python -m SimpleHTTPServer
      directory: /opt/web
      user: ubuntu
      stopsignal: HUP
```

## License

MIT
