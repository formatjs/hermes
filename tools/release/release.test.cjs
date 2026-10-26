const assert = require('node:assert/strict');
const {test} = require('node:test');
const {OverlayVersion} = require('./versions.cjs');
const {run} = require('./release.cjs');
const {TagName} = require('release-please/build/src/util/tag-name.js');

test('real tag parser preserves stable and snapshot BCR revisions', () => {
  const versions = [
    '260318099.0.0-393a539e6',
    '260318099.0.0-393a539e6.bcr.2',
    '260318099.0.0-393a539e6.bcr.10',
    '260318099.0.0',
    '260318099.0.0.bcr.2',
    '260318099.0.0.bcr.10',
    '260318099.0.1',
  ];
  assert.deepEqual(
    versions.slice().reverse().map(value => OverlayVersion.parse(value))
      .sort((left, right) => left.compare(right)).map(value => value.toString()),
    versions,
  );
  for (const version of versions) {
    assert.equal(TagName.parse(`v${version}`).toString(), `v${version}`);
    assert.equal(OverlayVersion.parse(`${version} (2026-10-25)\n\nChanges`).toString(), version);
  }
  for (const invalid of ['1.0.0.bcr.0', '1.0.0.bcr.01', '1.0.0-SHA.bcr.0', '1.0.0.bcr.2junk', '1.0.0+metadata', 'x1.0.0']) {
    assert.throws(() => OverlayVersion.parse(invalid));
  }
});

function configuration(version) {
  return {
    'release-type': 'hermes-overlay',
    'include-component-in-tag': false,
    'changelog-type': 'default',
    packages: {'.': {'package-name': 'hermes', 'release-as': version, prerelease: version.includes('-')}},
  };
}

// The real Manifest and Simple strategy run against this in-memory GitHub boundary.
class Repository {
  constructor(current, proposal) {
    this.repository = {owner: 'formatjs', repo: 'hermes', defaultBranch: 'main'};
    this.current = current;
    this.config = configuration(proposal);
    this.pullRequests = [];
    this.releases = [];
  }

  async getFileJson(path) {
    if (path === 'release-please-config.json') return this.config;
    if (path === '.release-please-manifest.json') return {'.': this.current};
    throw new Error(`Unexpected file request: ${path}`);
  }

  async *releaseIterator() {
    yield {tagName: `v${this.current}`, sha: 'previous-release', notes: ''};
  }

  async *tagIterator() {}

  async *mergeCommitIterator() {
    yield {sha: 'change', message: 'fix: preserve overlay version\n\nRelease-As: 999.0.0', files: ['tools/release/versions.cjs']};
    yield {sha: 'previous-release', message: 'chore: release', files: []};
  }

  async *pullRequestIterator(_branch, state) {
    if (state === 'MERGED' && this.merged) yield this.merged;
  }

  async createPullRequest(pullRequest, _branch, _message, updates) {
    const created = {...pullRequest, number: 7};
    this.pullRequests.push({created, updates});
    return created;
  }

  async createRelease(release, options) {
    this.releases.push({release, options});
    return {tagName: release.tag.toString(), sha: release.sha, url: 'https://example.test/release'};
  }

  async commentOnIssue() {}

  async removeIssueLabels(labels) {
    this.merged.labels = this.merged.labels.filter(label => !labels.includes(label));
  }

  async addIssueLabels(labels) {
    this.merged.labels.push(...labels);
  }
}

for (const [previous, proposed] of [
  ['0.0.0', '260318099.0.0-393a539e6'],
  ['260318099.0.0-393a539e6.bcr.2', '260318099.0.0-393a539e6.bcr.10'],
  ['260318099.0.4.bcr.2', '260318099.0.4.bcr.10'],
  ['260318099.0.0-fffffffff.bcr.2', '260318099.0.0-111111aaa'],
]) {
  test(`real release pipeline retains ${proposed} through PR, files, and tag`, async () => {
    const github = new Repository(previous, proposed);
    await run(github);
    assert.equal(github.pullRequests.length, 1);
    assert.equal(github.releases.length, 0);
    const {created, updates} = github.pullRequests[0];
    assert.equal(created.title, `chore(main): release ${proposed}`);
    const versionFile = updates.find(update => update.path === 'version.txt');
    assert.equal(versionFile.updater.updateContent(`${previous}\n`), `${proposed}\n`);
    const changelog = updates.find(update => update.path === 'CHANGELOG.md');
    assert.ok(changelog.updater.updateContent('# Changelog\n').includes(proposed));
    const manifest = updates.find(update => update.path === '.release-please-manifest.json');
    assert.deepEqual(JSON.parse(manifest.updater.updateContent(JSON.stringify({'.': previous}))), {'.': proposed});

    // Publication happens only after the release PR has been merged.
    github.current = proposed;
    github.merged = {...created, sha: 'approved-release-merge'};
    await run(github);
    assert.equal(github.releases.length, 1);
    assert.equal(github.releases[0].release.tag.toString(), `v${proposed}`);
    assert.equal(github.releases[0].options.prerelease, proposed.includes('-'));
    assert.equal(github.pullRequests.length, 1);

    await run(github);
    assert.equal(github.releases.length, 1);
    assert.equal(github.pullRequests.length, 1);
  });
}

test('unapproved version in a merged PR cannot create a tag', async () => {
  const version = '260318099.0.4.bcr.1';
  const github = new Repository('260318099.0.4', version);
  await run(github);
  github.current = version;
  github.merged = {...github.pullRequests[0].created, title: 'chore(main): release 999.0.0', sha: 'forged-merge'};
  await assert.rejects(() => run(github), /must match configured proposal/);
  assert.equal(github.releases.length, 0);
});

test('a regressed proposal cannot publish or open a release PR', async () => {
  const github = new Repository('260318099.0.4.bcr.10', '260318099.0.4.bcr.2');
  await assert.rejects(() => run(github), /precedes manifest/);
  assert.equal(github.releases.length, 0);
  assert.equal(github.pullRequests.length, 0);
});
