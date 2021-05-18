# Death Code

Death Code is an entirely self-hosted web application that utilizes [Shamir's Secret Sharing](https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing) to share secrets after you die. After splitting a secret among a group of people, the secret can only be reconstructed when a sufficient number of people combine their parts together, presumably only after you are gone from this earth. 

## Building

1. Install `git`, `docker`, and `docker-compose`
2. 

```bash
git clone https://github.com/andrewkdinh/death-code.git
git clone https://github.com/daniel-e/rust-captcha.git
cd death-code
cp .env.example .env
# Edit .env
docker-compose up -d
```
3. Visit `http://localhost:33284`

## Credits

- Built with Python Flask and Docker

Mirrors: [GitHub](https://github.com/andrewkdinh/death-code) (main), [Gitea](https://gitea.andrewkdinh.com/andrewkdinh/death-code)

Licensed under [AGPL](./LICENSE) | Copyright (c) 2021 Andrew Dinh
