# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-07

### Added
- Core language: lexer, parser, tree-walking evaluator.
- Flower-name token map (Glossary): keywords, brackets, punctuation, comparison, arithmetic, logical operators.
- String literal pair `bara_kuchi ... bara_tojiru`.
- Line comment `shion ...`.
- Statements: `sakura` (let), `yuri` (fn), `bara`/`tsubaki` (if/else), `ume` (while), `ran` (return).
- Builtins: `botan` (print), `ayame` (input).
- CLI: `floras run`, `floras repl`, `floras --version`, `--ast`, `--no-poesy` (flag reserved, no-op until v0.2.0).
- Examples: `hello.floras`, `fizzbuzz.floras`, `fib.floras`.
- Test suite covering lexer, parser, evaluator, and end-to-end examples.
