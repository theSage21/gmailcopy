GmailCopy
=========


- [x] Copy all mail in your gmail account locally.
- [ ] Browse and search through them locally via a small web server.

## Steps

1. Make sure IMAP is enabled on your email account.
2. Add a new application password in your gmail account.
3. Run `python -m gmailcopy --help` to see what all you can do.

## As a service

I have this running on my raspberry pi using Docker.

```
docker build -t gmailcopy .
docker run --user "$(id -u):$(id -g)" --detach -v $PWD:/src --restart always gmailcopy python -m gmailcopy.core --email <your-email>@gmail.com --pwd <gmail app password> --seconds 3600
```

## To view your emails


```
docker run -v $PWD:/src -p 5000:5000 gmailcopy python -m gmailcopy.server
```
