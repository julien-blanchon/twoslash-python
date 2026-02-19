import type { TwoslashShikiReturn } from '@shikijs/twoslash/core';
import fs from 'fs';
import type {
  CreateTwoslashOptions,
  TwoslashExecuteOptions,
} from 'twoslash';

export interface PythonCompilerOptions {}

export interface PythonSpecificOptions {
  /**
   * Python Compiler options
   */
  pythonCompilerOptions?: Partial<PythonCompilerOptions>;
}

export interface CreateTwoslashPythonOptions extends CreateTwoslashOptions, PythonSpecificOptions {
  /**
   * Render the generated code in the output instead of the Python file
   *
   * @default false
   */
  debugShowGeneratedCode?: boolean;
}

export interface TwoslashPythonExecuteOptions
  extends TwoslashExecuteOptions,
    PythonSpecificOptions {}

export interface PythonOptions {
  json_file_path: string | undefined;
}

type TwoslashShikiFunctionPython = {
  (
    code: string,
    lang?: string,
    options?: TwoslashExecuteOptions,
    pythonOptions?: PythonOptions
  ): TwoslashShikiReturn;
  getCacheMap: () => undefined;
};

function createTwoslasherPython(_createOptions: CreateTwoslashPythonOptions = {}) {
  const twoslasher: TwoslashShikiFunctionPython = (
    code: string,
    _extension?: string,
    _options?: TwoslashExecuteOptions,
    pythonOptions?: PythonOptions
  ): TwoslashShikiReturn => {
    const default_nodes = [
      {
        type: 'error' as const,
        id: '',
        code: 0,
        text: 'Parsing error: Unexpected token Foo',
        start: 1,
        length: 1,
        level: 'error' as const,
        filename: 'index.tsx',
        line: 0,
        character: 5,
      },
    ];

    if (!pythonOptions?.json_file_path) {
      return {
        code: code,
        nodes: default_nodes,
      };
    }

    const json_file_path = pythonOptions.json_file_path;

    // Load the json file
    let json_data;
    let nodes;
    try {
      json_data = fs.readFileSync(json_file_path, 'utf8');
      nodes = JSON.parse(json_data);
    } catch (error) {
      console.error('Error loading JSON file:', error);
      return {
        code: code,
        nodes: default_nodes,
      };
    }
    return {
      code: code,
      nodes: nodes,
    };
  };

  twoslasher.getCacheMap = () => {
    return undefined;
  };

  return twoslasher;
}

export { createTwoslasherPython, type TwoslashShikiFunctionPython };
