/* eslint-env node */
/**
 * Vue 3 + TypeScript：为 .vue 使用 vue-eslint-parser，脚本块由 @typescript-eslint/parser 解析。
 */
module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:vue/vue3-recommended",
    // 使用 eslint-recommended，避免对存量代码强制 no-explicit-any 等规则
    "plugin:@typescript-eslint/eslint-recommended",
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
  },
  plugins: ["@typescript-eslint"],
  overrides: [
    {
      files: ["*.vue"],
      parser: "vue-eslint-parser",
      parserOptions: {
        parser: "@typescript-eslint/parser",
        extraFileExtensions: [".vue"],
      },
      rules: {
        // 模板中常用 v-html，按项目需要可改为 warn 或单独禁用
        "vue/no-v-html": "off",
      },
    },
  ],
  rules: {
    // 由 @typescript-eslint/no-unused-vars 处理；避免在 .vue 中与基线规则重复报错
    "no-unused-vars": "off",
    "@typescript-eslint/no-unused-vars": [
      "warn",
      { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
    ],
  },
};
