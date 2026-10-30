// Usage: node z2m-split.js <dir with casaos configuration.yaml> <nix-generated zigbee2mqtt.yaml>
// Writes devices.yaml, groups.yaml, secret.yaml into <dir>; never prints secret values.
const fs = require("fs");
const path = require("path");
const yaml = require(process.env.JSYAML);
const [dir, nixFile] = process.argv.slice(2);
const c = yaml.load(fs.readFileSync(path.join(dir, "configuration.yaml"), "utf8"));
const n = yaml.load(fs.readFileSync(nixFile, "utf8"));

const secrets = {
  mqtt_password: c.mqtt.password,
  network_key: c.advanced.network_key,
  pan_id: c.advanced.pan_id,
  ext_pan_id: c.advanced.ext_pan_id,
};
for (const [k, v] of Object.entries(secrets)) if (v === undefined) throw new Error("missing " + k);

const w = (f, o, mode) => fs.writeFileSync(path.join(dir, f), yaml.dump(o), { mode });
w("devices.yaml", c.devices || {}, 0o644);
w("groups.yaml", c.groups || {}, 0o644);
w("secret.yaml", secrets, 0o600);

// Compare everything else: casaos minus split-out parts vs nix minus placeholders.
const strip = (o, isNix) => {
  const x = JSON.parse(JSON.stringify(o));
  delete x.devices; delete x.groups;
  delete x.mqtt.password;
  for (const k of ["network_key", "pan_id", "ext_pan_id"]) delete x.advanced[k];
  if (isNix) delete x.permit_join;
  return x;
};
const sort = (o) => (o && typeof o === "object" && !Array.isArray(o))
  ? Object.fromEntries(Object.keys(o).sort().map((k) => [k, sort(o[k])])) : o;
const a = JSON.stringify(sort(strip(c, false)));
const b = JSON.stringify(sort(strip(n, true)));
console.log("devices:", Object.keys(c.devices || {}).length, "groups:", Object.keys(c.groups || {}).length);
console.log("secret shapes:", Object.entries(secrets).map(([k, v]) => k + "=" + (Array.isArray(v) ? "array[" + v.length + "]" : typeof v)).join(" "));
console.log(a === b ? "SETTINGS MATCH" : "SETTINGS DIFFER\ncasaos: " + a + "\nnix:    " + b);
process.exit(a === b ? 0 : 2);
