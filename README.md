GmailCopy
=========


- [x] Copy all mail in your gmail account locally.
- [ ] Browse and search through them locally via a small web server.

## Steps

1. Make sure IMAP is enabled on your email account.
2. Add a new application password in your gmail account.
3. Run this code locally to copy all emails in the 'All mail' folder `python -m gmailcopy --email <your email> --pwd <app password>`

## As a service

I have this running on my raspberry pi using Docker.

```
docker build -t gmailcopy .
docker run --user "$(id -u):$(id -g)" --detach -v $PWD:/src --restart always python -m gmailcopy --email <your-email>@gmail.com --pwd <gmail app password>
```
