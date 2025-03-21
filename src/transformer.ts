/**
 * This file is the core of the @shikijs/twoslash package,
 * Decoupled from twoslash's implementation and allowing to introduce custom implementation or cache system.
 */
import type {
  CodeToHastOptions,
  ShikiTransformer,
  ShikiTransformerContext,
  ShikiTransformerContextMeta,
} from '@shikijs/types';
import type { Element, ElementContent, Text } from 'hast';
import type { TwoslashExecuteOptions, TwoslashGenericFunction } from 'twoslash';
import type { ModuleResolutionKind } from 'typescript';
import type {
  TransformerTwoslashOptions,
  TwoslashRenderer,
  TwoslashShikiFunction,
  TwoslashShikiReturn,
} from '@shikijs/twoslash/core';
import { splitTokens } from '@shikijs/core';
import { ShikiTwoslashError } from '@shikijs/twoslash/core';
import { rendererRichPython } from './renderer.js';
import { createTwoslasherPython } from './twoslasher.js';
import { type TwoslashShikiFunctionPython } from './twoslasher.js';
export function defaultTwoslashOptions(): TwoslashExecuteOptions {
  return {
    customTags: ['annotate', 'log', 'warn', 'error'],
    compilerOptions: {
      moduleResolution: 100 satisfies ModuleResolutionKind.Bundler,
    },
  };
}

interface TransformerTwoslashPythonOptions {
  langs?: string[];
  langAlias?: Record<string, string>;
  twoslasher: TwoslashShikiFunctionPython;
  explicitTrigger?: boolean | RegExp;
  disableTriggers?: string[];
  renderer?: TwoslashRenderer;
  throws?: boolean;
  onTwoslashError?: (
    error: Error,
    code: string,
    lang: string,
    options: TransformerTwoslashOptions
  ) => void;
  onShikiError?: (error: Error, source: string, lang: string) => void;
  // filter?: (lang: string | undefined, code: string, options: { meta: { json_file_path: undefined; __raw: string | string[] } }) => boolean,
  filter?: (
    lang: string | undefined,
    code: string,
    options: CodeToHastOptions<string, string>
  ) => boolean;
}

export function transformerTwoslashPython(
  options: TransformerTwoslashPythonOptions
): ShikiTransformer {
  const {
    langs = ['python'],
    langAlias = {
      python: 'python',
      py: 'python',
    },
    twoslasher = createTwoslasherPython(),
    explicitTrigger = false,
    disableTriggers = ['notwoslash', 'no-twoslash'],
    renderer = rendererRichPython(),
    throws = true,
  } = options;

  const onTwoslashError =
    options.onTwoslashError ||
    (throws
      ? (error) => {
          throw error;
        }
      : () => false);
  const onShikiError =
    options.onShikiError ||
    (throws
      ? (error) => {
          throw error;
        }
      : () => false);

  const trigger = explicitTrigger instanceof RegExp ? explicitTrigger : /\btwoslash\b/;

  if (!renderer) throw new ShikiTwoslashError('Missing renderer');

  const map = new WeakMap<ShikiTransformerContextMeta, TwoslashShikiReturn>();

  const {
    filter = (lang: string | undefined, _: any, options: CodeToHastOptions<string, string>) => {
      if (!lang) {
        return false;
      }
      return (
        langs.includes(lang) &&
        // Also filter that option.meta.json_file_path is not undefined
        options.meta?.json_file_path !== undefined &&
        (!explicitTrigger || (trigger as RegExp).test(String(options.meta?.__raw || ''))) &&
        !disableTriggers.some((i) =>
          typeof i === 'string'
            ? String(options.meta?.__raw || '').includes(i)
            : (i as RegExp).test(String(options.meta?.__raw || ''))
        )
      );
    },
  } = options;

  return {
    preprocess(code: string) {
      console.log('this.options.meta', this.options.meta);
      const lang = this.options.lang || '';
      const resolvedLang = lang in langAlias ? langAlias[lang] : lang;

      if (filter(resolvedLang, code, this.options)) {
        try {
          const codeWithIncludes = code;
          const twoslash = twoslasher(
            codeWithIncludes,
            lang,
            {},
            {
              json_file_path: this.options.meta?.json_file_path,
            }
          );
          map.set(this.meta, twoslash);
          this.meta.twoslash = twoslash;
          this.options.lang = twoslash.meta?.extension || lang;

          console.log('filter passed', code);
          return twoslash.code;
        } catch (error: unknown) {
          const result = onTwoslashError(error as Error, code, lang, {});
          if (typeof result === 'string') return code;
          else return undefined;
        }
      } else {
        console.log('filter failed', code);
        return code;
      }
    },
    tokens(tokens) {
      console.log('Starting tokens with tokens', tokens);
      const twoslash = map.get(this.meta);
      console.log('twoslash', twoslash);
      if (!twoslash) return;

      // Break tokens at the boundaries of twoslash nodes
      return splitTokens(
        tokens,
        twoslash.nodes.flatMap((i) =>
          ['hover', 'error', 'query', 'highlight', 'completion'].includes(i.type)
            ? [i.start, i.start + i.length]
            : []
        )
      );
    },
    pre(pre) {
      const twoslash = map.get(this.meta);
      if (!twoslash) return;
      this.addClassToHast(pre, 'twoslash lsp');
    },
    code(codeEl) {
      const twoslash = map.get(this.meta);
      if (!twoslash) return;

      const insertAfterLine = (line: number, nodes: ElementContent[]): void => {
        if (!nodes.length) return;
        let index: number;
        if (line >= this.lines.length) {
          index = codeEl.children.length;
        } else {
          const lineEl = this.lines[line];
          if (!lineEl) {
            onShikiError(
              new ShikiTwoslashError(`Cannot find line ${line} in code element`),
              this.source,
              this.options.lang
            );
            return;
          }
          index = codeEl.children.indexOf(lineEl);
          if (index === -1) {
            onShikiError(
              new ShikiTwoslashError(`Cannot find line ${line} in code element`),
              this.source,
              this.options.lang
            );
            return;
          }
        }

        // If there is a newline after this line, remove it because we have the error element take place.
        const nodeAfter = codeEl.children[index + 1];
        if (nodeAfter && nodeAfter.type === 'text' && nodeAfter.value === '\n')
          codeEl.children.splice(index + 1, 1);
        codeEl.children.splice(index + 1, 0, ...nodes);
      };

      // Build a map of tokens to their line and character position
      const tokensMap: [line: number, charStart: number, charEnd: number, token: Element | Text][] =
        [];
      this.lines.forEach((lineEl, line) => {
        let index = 0;
        for (const token of lineEl.children.flatMap((i) =>
          i.type === 'element' ? i.children || [] : []
        ) as (Text | Element)[]) {
          if ('value' in token && typeof token.value === 'string') {
            tokensMap.push([line, index, index + token.value.length, token]);
            index += token.value.length;
          }
        }
      });

      // Find tokens are in range of a node, it can may multiple tokens.
      const locateTextTokens = (
        line: number,
        character: number,
        length: number
      ): (Element | Text)[] => {
        const start = character;
        const end = character + length;
        // When the length is 0 (completion), we find the token that contains it
        if (length === 0) {
          return tokensMap
            .filter(([l, s, e]) => l === line && s < start && start <= e)
            .map((i) => i[3]);
        }
        // Otherwise we find the tokens that are completely inside the range
        // Because we did the breakpoints earlier, we can safely assume that there will be no across-boundary tokens
        return tokensMap
          .filter(([l, s, e]) => l === line && start <= s && s < end && start < e && e <= end)
          .map((i) => i[3]);
      };

      const tokensSkipHover = new Set<Element | Text>();
      const actionsHovers: (() => void)[] = [];
      const actionsHighlights: (() => void)[] = [];

      for (const node of twoslash.nodes) {
        if (node.type === 'tag') {
          if (renderer.lineCustomTag)
            insertAfterLine(node.line, renderer.lineCustomTag.call(this, node));
          continue;
        }

        const tokens = locateTextTokens(node.line, node.character, node.length);

        if (!tokens.length && !(node.type === 'error' && renderer.nodesError)) {
          onShikiError(
            new ShikiTwoslashError(`Cannot find tokens for node: ${JSON.stringify(node)}`),
            this.source,
            this.options.lang
          );
          continue;
        }

        // Wrap tokens with new elements, all tokens has to be in the same line
        const wrapTokens = (fn: (children: ElementContent[]) => ElementContent[]): void => {
          const line = this.lines[node.line];
          if (!line) {
            onShikiError(
              new ShikiTwoslashError(`Cannot find line ${node.line} in code element`),
              this.source,
              this.options.lang
            );
            return;
          }
          let charIndex = 0;
          let itemStart = line.children.length;
          let itemEnd = 0;

          line.children.forEach((token, index) => {
            if (charIndex >= node.character && index < itemStart) itemStart = index;
            if (charIndex <= node.character + node.length && index > itemEnd) itemEnd = index;
            charIndex += getTokenString(token).length;
          });

          if (charIndex <= node.character + node.length) itemEnd = line.children.length;

          const targets = line.children.slice(itemStart, itemEnd);
          const length = targets.length;
          line.children.splice(itemStart, length, ...fn(targets));
        };

        switch (node.type) {
          case 'error': {
            console.log('error node', node);
            if (renderer.nodeError) {
              tokens.forEach((token) => {
                tokensSkipHover.add(token);
                const clone = { ...token };
                Object.assign(token, renderer.nodeError!.call(this, node, clone));
              });
            }
            if (renderer.nodesError) {
              tokens.forEach((token) => {
                tokensSkipHover.add(token);
              });
              actionsHighlights.push(() => {
                wrapTokens((targets) => renderer.nodesError?.call(this, node, targets) || targets);
              });
            }
            if (renderer.lineError) insertAfterLine(node.line, renderer.lineError.call(this, node));
            break;
          }
          case 'query': {
            const token = tokens[0];
            if (token && renderer.nodeQuery) {
              tokensSkipHover.add(token);
              const clone = { ...token };
              Object.assign(token, renderer.nodeQuery!.call(this, node, clone));
            }
            if (renderer.lineQuery)
              insertAfterLine(node.line, renderer.lineQuery.call(this, node, token));
            break;
          }
          case 'completion': {
            if (renderer.nodeCompletion) {
              tokens.forEach((token) => {
                tokensSkipHover.add(token);
                const clone = { ...token };
                Object.assign(token, renderer.nodeCompletion!.call(this, node, clone));
              });
            }
            if (renderer.lineCompletion)
              insertAfterLine(node.line, renderer.lineCompletion.call(this, node));
            break;
          }
          case 'highlight': {
            if (renderer.nodesHighlight) {
              actionsHighlights.push(() => {
                wrapTokens(
                  (targets) => renderer.nodesHighlight?.call(this, node, targets) || targets
                );
              });
            }
            break;
          }
          case 'hover': {
            // Hover will be handled after all other nodes are processed
            if (renderer.nodeStaticInfo) {
              actionsHovers.push(() => {
                tokens.forEach((token) => {
                  if (tokensSkipHover.has(token)) return;
                  // Already hovered, don't hover again
                  tokensSkipHover.add(token);
                  const clone = { ...token };
                  Object.assign(token, renderer.nodeStaticInfo.call(this, node, clone));
                });
              });
            }
            break;
          }
          default: {
            onShikiError(
              new ShikiTwoslashError(`Unknown node type: ${(node as any)?.type}`),
              this.source,
              this.options.lang
            );
          }
        }
      }

      actionsHovers.forEach((i) => i());
      actionsHighlights.forEach((i) => i());
    },
  };
}

function getTokenString(token: ElementContent): string {
  if ('value' in token) return token.value;
  return token.children?.map(getTokenString).join('') || '';
}
