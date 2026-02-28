module.exports = {
  root: true,
  env: { 
    browser: true, 
    es2020: true,
    node: true, // Add node environment for vite.config.ts
  },
  extends: [
    'eslint:recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs', 'node_modules'],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  plugins: ['@typescript-eslint', 'react-hooks', 'react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    '@typescript-eslint/no-unused-vars': 'warn',
    'no-unused-vars': 'off', // Turn off base rule as it can report incorrect errors
    'no-undef': 'off', // Turn off for TypeScript files as TypeScript handles this
    'no-useless-catch': 'warn', // Change to warning instead of error
    'no-useless-escape': 'warn', // Change to warning instead of error
  },
  settings: {
    react: {
      version: 'detect',
      runtime: 'automatic', // For new JSX transform
    },
  },
  // Override rules for specific file types
  overrides: [
    {
      files: ['*.ts', '*.tsx'],
      rules: {
        'no-undef': 'off', // TypeScript handles undefined variables
      },
    },
  ],
} 