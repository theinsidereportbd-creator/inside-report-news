# The International Inside Report — News Desk

A live headline page that updates itself. It collects headlines and links from
newspapers, portals and TV channels around the world, and shows them in one
searchable list.

## How it works

1. `feeds.json` lists the outlets and their RSS feed addresses.
2. A GitHub Actions job runs `scripts/fetch_news.py` every 20 minutes. It reads
   every feed and writes `docs/news.json`.
3. `docs/index.html` is the page. It loads `news.json` and checks for a new copy
   every 5 minutes while it is open.

Only the headline, link, outlet and time are stored. Readers click through to the
outlet for the full story.

## Set it up (about 10 minutes)

1. Create a new GitHub repository (public is simplest) and upload everything in
   this folder, including the hidden `.github` folder.
2. In the repository, open **Settings → Pages**. Under "Build and deployment" choose
   **Deploy from a branch**, branch `main`, folder `/docs`, then Save.
3. Open the **Actions** tab, choose **Update news**, and press **Run workflow**
   once. After about a minute `docs/news.json` appears.
4. Your page is at `https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/`.

From then on it updates by itself.

## Install it as an app on a phone

The page is an installable web app. Open your page address in Chrome on Android:

1. Tap **Install app** on the page, or open the Chrome menu (three dots) and choose
   **Install app** or **Add to Home screen**.
2. Open it from the new "Inside Report" icon on the home screen. It opens full screen.

It also opens without internet and shows the last saved headlines. On iPhone, open the
page in Safari, tap Share, then **Add to Home Screen**.

The page has a **বাংলা | English** switch at the top right. It translates the page
labels only. Headlines stay in each outlet's own language.

## Add or remove outlets

Edit `feeds.json`. Each entry needs `name`, `region`, `type` and `url` (the RSS
address). To find an outlet's feed, look for an "RSS" link in its footer or try
`/rss` or `/feed` after the site address. A feed that fails is skipped and shown
as "offline" in the Outlets list, so one broken address never stops the page.

An entry can also set `"max_age_days"` to keep older items than the default 3 days.
The channel's own YouTube feed uses 30 days so recent videos stay visible.

## Known limits

- Some outlets change or remove their feeds without notice. Check the Outlets list
  now and then and fix or replace any marked offline.
- Public repositories pause scheduled jobs after 60 days with no activity. If the
  page shows a "has not updated" notice, open Actions and re-enable the workflow.
- Every update is a small commit, so the repository history grows over time.
- Feed addresses in `feeds.json` come from memory and were not tested against the
  live sites. The first run will show which ones answer.

## Check before you publish

A headline here is a lead from another outlet, not a confirmed fact. Open the
source, find a second independent source, and follow your own verification
checklist before you republish anything.
