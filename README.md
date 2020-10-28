GmailCopy
=========


- [x] Copy all mail in your gmail account locally.
    - [x] Attachments
    - [x] Gmail labels applied to the emails.
- [x] Browse through email locally via a small web server.
- [ ] Search local copy using text search + labels.

## Steps

1. Make sure IMAP is enabled on your email account.
2. Add a new application password in your gmail account.
3. Install docker on your system.

## Run as a service

I have this running on my raspberry pi using Docker.

```
docker build -t gmailcopy .
docker run --user "$(id -u):$(id -g)" --detach -v $PWD:/src --restart always gmailcopy python -m gmailcopy.core --email <your-email>@gmail.com --pwd <gmail app password> --seconds 3600
```

## To browse locally


```
docker run -v $PWD:/src -p 5000:5000 gmailcopy python -m gmailcopy.server
```
Then visit http://localhost:5000 in your browser.
