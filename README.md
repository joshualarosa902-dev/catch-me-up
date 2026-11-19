# Catch Me Up

**Name a topic and a time window. Claude scrolls the internet for you and hands back the few
posts worth seeing, with links.**

> **Free and open source.** No account, no API key, no credits. It runs in Claude Code and uses
> only free public feeds.
>
> **Honest limit, up front:** there is no free way to read X, TikTok or Reddit. Catch Me Up tries
> Claude's web search for them, which often finds little, and it tells you when that happens.
> Details in [What it reads](#what-it-reads).

Hey, I'm Joshua ([@joshualarosa.ai](https://www.instagram.com/joshualarosa.ai/) on Instagram). I
built Catch Me Up because keeping up with one topic means opening six apps and losing an hour.
This does the scrolling for you and gives you a one-screen briefing instead. It's free, and it
stays free.

**Jump to:** [What it does](#what-it-does) · [Install](#install) · [How to use it](#how-to-use-it) ·
[What you get](#what-you-get) · [What it reads](#what-it-reads) · [What to expect](#what-to-expect) ·
[Privacy](#privacy) · [Troubleshooting](#troubleshooting) · [Credits](#credits)

## What it does

1. **You name a topic and a window.** "GTA 6, last 24 hours." "New AI tool launches, last 3 days."
2. **Claude writes the searches.** It covers the different spellings people use.
3. **A script reads the free sources at the same time:** Hacker News, YouTube, Bluesky, Google
   News, GitHub, Mastodon and Product Hunt. It also tries Reddit once.
4. **The script cleans up.** It drops posts older than your window, removes duplicates, and
   leaves out anything it already showed you for that topic.
5. **Claude tries the gaps.** It runs a few web searches for X, TikTok and Reddit. If it finds
   real recent posts it adds them with a mark. Often it finds none, and the briefing says so.
6. **Claude writes the briefing.** It throws out junk and ads, groups posts into stories, and
   gives you 3 to 7 stories, a short "worth opening" list, the mood, and a coverage line that says
   what was and was not read.

Ask again later with "what's new?" and you only get what appeared since last time.

## Install

You need [Claude Code](https://claude.com/claude-code) and Python 3.8 or newer (a Mac already has
it). In Claude Code, run:

```
/plugin marketplace add joshualarosa902-dev/catch-me-up
/plugin install catch-me-up@catch-me-up
```

Choose **Install for you (user scope)**, then start a new session.

Rather not type commands? Paste this into Claude Code and let Claude do the setup:

```
https://github.com/joshualarosa902-dev/catch-me-up  Install this skill, then confirm /catch-me-up works.
```

Or as one line in a terminal:

```
claude plugin marketplace add joshualarosa902-dev/catch-me-up && claude plugin install catch-me-up@catch-me-up
```

The first time it runs, Claude Code asks permission to run the script. Pick the option that stops
it asking again for this session.

## How to use it

```
/catch-me-up GTA 6, last 24 hours
```

Or just say it: "Catch me up on the new Claude model since yesterday."

- **Window:** hours, days or weeks. If you don't give one, it uses the last 24 hours.
- **"What's new?"** Ask about the same topic again and you get only new posts.
- **Start over:** say "show me everything again" or "forget what I've seen about GTA 6".
- If `/catch-me-up` doesn't show up, use the full name: `/catch-me-up:catch-me-up`.

## What you get

A briefing shaped like this (the layout, not real results):

```
**<Topic>: last 24h**
<N> posts collected from Hacker News, YouTube, Bluesky, Google News, top 40 read · $0, no API keys

**1. <What happened, in plain words>**
<Why people care, with the strongest quote or number>
Seen on: YouTube, Hacker News · <link>

**2. ...**

**Worth opening**
- <a video or thread> (<why it is worth the click>) <link>

**The mood:** <how people feel, with one real quote and its link>

**Coverage:** <what was read>. Not covered: <what was skipped or blocked>.
```

Every story has a link. If the window was quiet, it says so in one line instead of padding.

## What it reads

| Source | How | Free, no key | Good to know |
|---|---|---|---|
| Hacker News | Public search API | Yes | Points and comment counts |
| YouTube | Public search page | Yes | View counts; times are estimates ("about 3h ago"). Could break if YouTube changes its page. |
| Bluesky | Public search API | Yes | Likes, replies, reposts |
| Google News | Public RSS feed | Yes | Headlines only, no numbers |
| GitHub | Public search API | Yes | New repositories, by stars. Limited to a few searches a minute, so it can show as blocked if you run several times in a row. |
| Mastodon | Public hashtag feed (mastodon.social) | Yes | Only posts that use the topic as a hashtag |
| Product Hunt | Public feed | Yes | Recent launches, no vote counts |
| Reddit | Public search | Usually blocked | Reddit turns away most visitors who aren't signed in. When that happens the briefing says so. |
| X, TikTok | Claude's web search | Rarely | No free route exists. Web search sometimes turns up a few posts (no like counts, labeled with a star). In my launch-day test it found none. |

If a source fails, it is skipped and named on the coverage line. Nothing is hidden.

## What to expect

> - **Cost:** $0 beyond your normal Claude plan usage. No credits, no wallet, no sign-up.
> - **Time:** the script itself takes a few seconds. The whole briefing takes a few minutes,
>   mostly Claude reading and writing.
> - **It is a sample, not everything.** Each source returns its top few dozen results, and Claude
>   reads the top 40 of what was collected. Big topics have far more posts than any one run reads.
> - **Headlines are headlines.** News and Hacker News come back as titles. Claude says when a
>   story rests on a headline it did not open.
> - **Search is loose.** Sources match words, not meaning, so some results are off topic. Claude
>   filters them out before writing the briefing.
> - **Nothing made up.** No invented quotes, numbers or links. That's the rule the skill is built
>   around.

## Privacy

> - **No account, no tracking.** The script makes plain read requests to the public sources in
>   the table above and nothing else. Your topic is sent to those sources as a search, the same as
>   if you typed it into their search box.
> - **What stays on your computer:** a `~/.catch-me-up` folder with the list of links you have
>   already been shown (per topic) and a copy of each run. Delete it any time.
> - **Your Claude settings still apply.** The conversation is a normal Claude Code session.

## Troubleshooting

| What you see | Try this |
|---|---|
| Claude doesn't use Catch Me Up | Say "Use Catch Me Up" or type `/catch-me-up`. Start a new session after installing. |
| "reddit blocked" on the coverage line | Normal. Reddit blocks most visitors who aren't signed in. |
| "youtube failed (search page not readable)" | YouTube sometimes sends back an empty page. Try again in a minute. If it fails every time, YouTube changed its page: please [open an issue](https://github.com/joshualarosa902-dev/catch-me-up/issues). The other sources still work. |
| "0 posts kept" on a second run | It already showed you those. Say "show me everything again". |
| Lots of unrelated results | Give a more exact topic ("Cursor code editor", not "Cursor"). |
| `python3: command not found` | Install Python 3 from [python.org](https://www.python.org/downloads/). |

## For developers

The whole thing is one instruction file and one standard-library Python script:

- [SKILL.md](plugins/catch-me-up/skills/catch-me-up/SKILL.md): what Claude does
- [cmu.py](plugins/catch-me-up/skills/catch-me-up/scripts/cmu.py): fetch, filter, deduplicate, score

```
python3 plugins/catch-me-up/skills/catch-me-up/scripts/cmu.py scroll --topic "GTA 6" --q "GTA 6" --q "GTA VI" --since 24h
sh scripts/check.sh
```

`check.sh` runs the offline tests. They need no network.

## Credits

The idea comes from the **doomscroll** skill by Jason Zhou
([@jasonzhou1993](https://x.com/jasonzhou1993)) and the Superdesign team, part of
[superdesigndev/treg](https://github.com/superdesigndev/treg). I saw it in
[his post](https://x.com/jasonzhou1993/status/2123386390658634096) and wanted a version anyone
could run with no account.

The two are built differently. doomscroll runs on treg, a paid tool catalog, which is how it reads
X and TikTok properly. Catch Me Up is a from-scratch build that uses none of treg's code or text
and only free public feeds, so it costs nothing but covers X and TikTok less well. If you need
those two done right, use theirs. Thank you, Jason, for the idea.

---

MIT License ([LICENSE](LICENSE)) · Not affiliated with Anthropic or any of the sources it reads ·
Third-party credits in [NOTICE](NOTICE) · Version 1.0.0 ([CHANGELOG](CHANGELOG.md))
