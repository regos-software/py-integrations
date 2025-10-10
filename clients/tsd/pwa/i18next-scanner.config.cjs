const fs = require("fs");
const chalk = require("chalk");

module.exports = {
  input: [
    "src/**/*.{js,jsx}",
    // Use ! to filter out files or directories
    "!src/**/*.spec.{js,jsx}",
    "!src/renderer/i18n/**",
    "!**/node_modules/**",
  ],
  options: {
    sort: true,
    debug: true,
    func: {
      extensions: [".js", ".jsx"],
      list: ["t", "props.t", "i18n.t"],
      fallbackKey: false,
    },
    trans: false,
    lngs: ["ru", "uz", "en"],
    ns: [],
    defaultLng: "ru",
    defaultNs: "",
    defaultValue(lng, namespace, value) {
      return value;
    },
    resource: {
      loadPath: "./assets/i18n/{{lng}}.json",
      savePath: "./assets/i18n/{{lng}}.json",
      jsonIndent: 2,
      lineEnding: "\n",
    },
    nsSeparator: false, // namespace separator
    keySeparator: false, // key separator
    interpolation: {
      prefix: "{{",
      suffix: "}}",
    },
    metadata: {},
    allowDynamicKeys: false,
  },
};
