// The newest release of a kind (M-Film's v*, Darkrooms' app-v*), from GitHub's
// API. Both are published in the same repository, so "releases/latest" can be
// either: this looks for the right one. Kept for an hour in sessionStorage.

const API = 'https://api.github.com/repos/HNGSeries/mfilm-canon-film-simulation/releases?per_page=30';
let list = null;

async function releases() {
  if (list) return list;
  try {
    const kept = JSON.parse(sessionStorage.getItem('mfilm.releases') || 'null');
    if (kept && Date.now() - kept.t < 3600e3) return (list = kept.list);
  } catch {}
  const r = await fetch(API, { headers: { accept: 'application/vnd.github+json' } });
  if (!r.ok) throw new Error('GitHub ' + r.status);
  list = (await r.json())
    .filter((x) => !x.draft && !x.prerelease)
    .map((x) => ({ tag: x.tag_name, at: x.published_at,
                   assets: x.assets.map((a) => ({ name: a.name, browser_download_url: a.browser_download_url })) }));
  try { sessionStorage.setItem('mfilm.releases', JSON.stringify({ t: Date.now(), list })); } catch {}
  return list;
}

// the newest whose tag passes the test, or null (no answer from GitHub, or none)
export async function latestRelease(test) {
  try {
    const all = (await releases()).filter((x) => test(x.tag));
    all.sort((a, b) => (a.at < b.at ? 1 : -1));
    return all[0] || null;
  } catch (e) {
    console.warn('releases:', e);
    return null;
  }
}
