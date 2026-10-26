const versionApi = require('release-please/build/src/version.js');
const SemanticVersion = versionApi.Version;

class OverlayVersion extends SemanticVersion {
  static parse(input) {
    // Release Please also parses the dated heading from a release PR's body.
    const heading = /^(\S+) \(\d{4}-\d{2}-\d{2}\)(?:\r?\n|$)/.exec(input);
    const text = heading ? heading[1] : input;
    const marker = text.lastIndexOf('.bcr.');
    const revisionText = marker < 0 ? '' : text.slice(marker + 5);
    if (marker >= 0 && (!/^[1-9][0-9]*$/.test(revisionText) || text.indexOf('.bcr.') !== marker)) {
      throw new Error(`Invalid overlay revision: ${input}`);
    }
    const base = marker < 0 ? text : text.slice(0, marker);
    const revision = marker < 0 ? 0 : Number(revisionText);
    const semantic = SemanticVersion.parse(base);

    // The upstream parser accepts partial matches and would drop a stable suffix.
    if (semantic.toString() !== base || semantic.build || !Number.isSafeInteger(revision)) {
      throw new Error(`Invalid overlay version: ${input}`);
    }
    semantic.compare(semantic);
    const result = new OverlayVersion(semantic.major, semantic.minor, semantic.patch, semantic.preRelease);
    result.revision = revision;
    return result;
  }

  toString() {
    return super.toString() + (this.revision ? `.bcr.${this.revision}` : '');
  }

  get sourceVersion() {
    return super.toString();
  }

  compare(other) {
    const left = new SemanticVersion(this.major, this.minor, this.patch, this.preRelease);
    const right = new SemanticVersion(other.major, other.minor, other.patch, other.preRelease);
    return left.compare(right) || Math.sign((this.revision || 0) - (other.revision || 0));
  }
}

// Install before loading strategies so tags, PR bodies, and manifests agree.
versionApi.Version = OverlayVersion;
module.exports = {OverlayVersion};
