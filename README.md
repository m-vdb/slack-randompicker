![Continuous Integration](https://github.com/m-vdb/slack-randompicker/workflows/Continuous%20Integration/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/m-vdb/slack-randompicker/badge.svg?branch=master)](https://coveralls.io/github/m-vdb/slack-randompicker?branch=master)

# slack-randompicker
Pick a random person from a group or channel in Slack


## Installation

After creatinga Slack bot, you can install `slack-randompicker` using `docker` on your own server. Required
environment variables are documented in the `Dockerfile`.

## Slack app setup

Assuming your Slackbot is installed at `https://host.com`, to setup the bot for your own workspace, you will need the following:

- *Interactivity*: set the request URL to `https://host.com/actions`
- *Slash commands*: create a new slash command named `/pickrandom` and set the request URL to `https://host.com/slashcommand`
- *Bot Token Scopes*: set up the scopes `channels:read`, `chat:write`, `chat:write.public`, `commands`, `groups:read`, `usergroups:read` and `users:read`.
