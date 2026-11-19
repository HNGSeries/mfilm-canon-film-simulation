// The newest release of a kind, from GitHub's API: M-Film's (v*) in M-Film's repository, Darkrooms'
// (app-v*) in its own, darkrooms-app. Darkrooms up to 0.2.2 was published in M-Film's repository too,
// and those releases stay there, so M-Film's are still picked by tag. Kept for an hour in sessionStorage.

export const MFILM = 'HNGSeries/mfilm-canon-film-simulation';
export const DARKROOMS = 'HNGSeries/Darkrooms-app';
const lists = {};

async function releases(repo) {
  if (lists[repo]) return lists[repo];
  const key = repo === MFILM ? 'mfilm.releases' : 'mfilm.releases.' + repo;
  try {
    const kept = JSON.parse(sessionStorage.getItem(key) || 'null');
    if (kept && Date.now() - kept.t < 3600e3) return (lists[repo] = kept.list);
  } catch {}
  const r = await fetch(`https://api.github.com/repos/${repo}/releases?per_page=30`,
                        { headers: { accept: 'application/vnd.github+json' } });
  if (!r.ok) throw new Error('GitHub ' + r.status);
  const list = (lists[repo] = (await r.json())
    .filter((x) => !x.draft && !x.prerelease)
    .map((x) => ({ tag: x.tag_name, at: x.published_at,
                   assets: x.assets.map((a) => ({ name: a.name, browser_download_url: a.browser_download_url })) })));
  try { sessionStorage.setItem(key, JSON.stringify({ t: Date.now(), list })); } catch {}
  return list;
}

// the newest in a repository (M-Film's unless named) whose tag passes the test, or null
// (no answer from GitHub, or none)
export async function latestRelease(test, repo = MFILM) {
  try {
    const all = (await releases(repo)).filter((x) => test(x.tag));
    all.sort((a, b) => (a.at < b.at ? 1 : -1));
    return all[0] || null;
  } catch (e) {
    console.warn('releases:', e);
    return null;
  }
}

// a camera's zip in a release: M-Film-<version>-camera-<platform>.zip since 0.2.4,
// M-Film-camera-<platform>.zip before. { name, browser_download_url }, or null
export function cameraZip(release, platform) {
  if (!release) return null;
  const tail = `camera-${platform}.zip`;
  return release.assets.find((a) => a.name === `M-Film-${tail}` ||
    (a.name.endsWith(`-${tail}`) && /^M-Film-\d[\w.]*$/.test(a.name.slice(0, -tail.length - 1)))) || null;
}
