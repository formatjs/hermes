const {OverlayVersion} = require('./versions.cjs');
const {GitHub, Manifest, registerReleaseType} = require('release-please');
const {Simple} = require('release-please/build/src/strategies/simple.js');

class ProposedRelease extends Simple {
  constructor(options) {
    super(options);
    if (!options.releaseAs) throw new Error('An upstream-derived release-as is required');
    this.proposal = OverlayVersion.parse(options.releaseAs);
  }

  async buildRelease(pullRequest, options) {
    const candidate = await super.buildRelease(pullRequest, options);
    if (candidate && candidate.tag.version.toString() !== this.proposal.toString()) {
      throw new Error(`Release candidate must match configured proposal ${this.proposal}`);
    }
    return candidate;
  }
}

registerReleaseType('hermes-overlay', options => new ProposedRelease(options));

async function run(github, branch = github.repository.defaultBranch) {
  const config = await github.getFileJson('release-please-config.json', branch);
  const proposal = OverlayVersion.parse(config.packages['.']['release-as']);
  const load = () => Manifest.fromManifest(github, branch, 'release-please-config.json', '.release-please-manifest.json');
  const manifest = await load();
  const current = manifest.releasedVersions['.'];
  // Snapshot hashes do not encode commit order; only revisions share an ordering.
  if (!current || (proposal.sourceVersion === current.sourceVersion && proposal.compare(current) < 0)) {
    throw new Error(`Release proposal ${proposal} precedes manifest ${current}`);
  }

  // An approved, merged release PR still needs publication when versions match.
  await manifest.createReleases();
  if (proposal.compare(current) === 0) {
    console.log(`Release proposal ${proposal} already recorded; no new PR`);
    return;
  }
  await (await load()).createPullRequests();
}

module.exports = {ProposedRelease, run};

if (require.main === module) {
  (async () => {
    const token = process.env.GH_TOKEN;
    const repository = process.env.GITHUB_REPOSITORY;
    if (!token || !/^[\w.-]+\/[\w.-]+$/.test(repository || '')) {
      throw new Error('GH_TOKEN and GITHUB_REPOSITORY=owner/repository are required');
    }
    const [owner, repo] = repository.split('/');
    const github = await GitHub.create({owner, repo, token});
    await run(github);
  })().catch(error => {
    console.error(error);
    process.exitCode = 1;
  });
}
