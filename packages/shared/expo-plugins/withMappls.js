/**
 * Expo config plugin for Mappls (MapmyIndia) React-Native SDK — Android.
 *
 * What it does at `expo prebuild` time:
 *   1. Adds the Mappls maven repository to android/build.gradle (allprojects) and
 *      android/settings.gradle (dependencyResolutionManagement) when present.
 *   2. Copies the Mappls account files `<applicationId>.a.conf` and `<applicationId>.a.olf`
 *      (downloaded from https://auth.mappls.com/console) into android/app/.
 *      Location is configurable: plugin option `configDir` (default: "<project>/mappls").
 *   3. Ensures INTERNET + location permissions are declared.
 *
 * Usage in app.json:
 *   "plugins": [["../../packages/shared/expo-plugins/withMappls.js", { "configDir": "./mappls" }]]
 */
const fs = require('fs');
const path = require('path');
const {
  withProjectBuildGradle,
  withSettingsGradle,
  withDangerousMod,
  withAndroidManifest,
  AndroidConfig,
} = require('expo/config-plugins');

const MAVEN_URL = 'https://maven.mappls.com/repository/mappls/';
const MAVEN_SNIPPET = `maven { url '${MAVEN_URL}' }`;

function addMavenToProjectGradle(contents) {
  if (contents.includes(MAVEN_URL)) return contents;
  // Prefer allprojects { repositories { ... } }
  const allprojects = /allprojects\s*\{\s*repositories\s*\{/;
  if (allprojects.test(contents)) {
    return contents.replace(allprojects, (m) => `${m}\n        ${MAVEN_SNIPPET}`);
  }
  return `${contents}\n\nallprojects {\n    repositories {\n        ${MAVEN_SNIPPET}\n    }\n}\n`;
}

function addMavenToSettingsGradle(contents) {
  if (contents.includes(MAVEN_URL)) return contents;
  const drm = /dependencyResolutionManagement\s*\{[\s\S]*?repositories\s*\{/;
  if (drm.test(contents)) {
    return contents.replace(drm, (m) => `${m}\n        ${MAVEN_SNIPPET}`);
  }
  return contents;
}

const withMapplsGradle = (config) => {
  config = withProjectBuildGradle(config, (cfg) => {
    if (cfg.modResults.language === 'groovy') {
      cfg.modResults.contents = addMavenToProjectGradle(cfg.modResults.contents);
    }
    return cfg;
  });
  config = withSettingsGradle(config, (cfg) => {
    cfg.modResults.contents = addMavenToSettingsGradle(cfg.modResults.contents);
    return cfg;
  });
  return config;
};

const withMapplsAccountFiles = (config, { configDir }) =>
  withDangerousMod(config, [
    'android',
    async (cfg) => {
      const projectRoot = cfg.modRequest.projectRoot;
      const appDir = path.join(cfg.modRequest.platformProjectRoot, 'app');
      const appId = cfg.android && cfg.android.package;
      const source = path.resolve(projectRoot, configDir || 'mappls');
      const wanted = [`${appId}.a.conf`, `${appId}.a.olf`];
      let copied = 0;
      for (const name of wanted) {
        const from = path.join(source, name);
        if (fs.existsSync(from)) {
          fs.copyFileSync(from, path.join(appDir, name));
          copied += 1;
        }
      }
      if (copied < wanted.length) {
        // Not fatal: the map will raise onMapError until the files are added.
        console.warn(
          `\n[withMappls] Missing Mappls account files in ${source}.\n` +
            `           Download ${wanted.join(' and ')} from https://auth.mappls.com/console\n` +
            `           (register package "${appId}" + your signing SHA-256) and place them there.\n`,
        );
      }
      return cfg;
    },
  ]);

const withMapplsPermissions = (config) =>
  withAndroidManifest(config, (cfg) => {
    const perms = [
      'android.permission.INTERNET',
      'android.permission.ACCESS_NETWORK_STATE',
      'android.permission.ACCESS_COARSE_LOCATION',
      'android.permission.ACCESS_FINE_LOCATION',
    ];
    for (const p of perms) AndroidConfig.Permissions.addPermission(cfg.modResults, p);
    return cfg;
  });

module.exports = function withMappls(config, props = {}) {
  config = withMapplsGradle(config);
  config = withMapplsAccountFiles(config, props);
  config = withMapplsPermissions(config);
  return config;
};
