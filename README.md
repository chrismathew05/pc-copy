# PC

NOTE: This is not the full project repository; it contains only a small SAMPLE of files for presentation purposes only.

This project scrapes various sources (Yahoo Finance, Tipranks, Questrade, etc.) and tracks daily/intraday metrics on stocks from the following markets: CSE, TSX, TSXV, NASDAQ, NYSE. A scoring algorithm is continuously run, sending us notifications of what to buy/sell.

## Links

- Link to Web App: [REDACTED - hosted on vercel]
- Link to Documentation (once logged in): [REDACTED - hosted on vercel]
- Link to Web App repo: https://github.com/chrismathew05/pc-copy

## Building

The build script `build.sh` has the following options:

```
# re-build container + run unit tests
./build.sh

# re-build container + run local file z.py
./build.sh "z"

# re-build container + run in interactive mode
./build.sh "it"

# re-build container, re-build docs/transfer to web app repo, upload to ECR and connect to Lambda
./build.sh "up"
```

## Architecture

Process flow chart:

![Process Chart](https://lucid.app/publicSegments/view/4751ca84-1391-43bd-85a8-5fc1ee6314da/image.png "Process Chart")

## TODO

- [ ] REDACTED

## Scratch

[REDACTED]
