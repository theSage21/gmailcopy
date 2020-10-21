GmailCopy
=========


- [x] Copy all mail in your gmail account locally.
- [ ] Browse and search through them locally via a small web server.

```
docker build -t gmailcopy .
# Run this on a raspberry pi or something to maintain a forever-copy of your email
docker run --user "$(id -u):$(id -g)" --detach -v $PWD:/src --restart always python -m gmailcopy --email <your-email>@gmail.com --pwd <gmail app password>
```
