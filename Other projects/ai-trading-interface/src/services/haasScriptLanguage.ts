import * as monaco from 'monaco-editor';

// HaasScript language configuration
export const haasScriptLanguageConfig: monaco.languages.LanguageConfiguration = {
  comments: {
    lineComment: '//',
    blockComment: ['/*', '*/']
  },
  brackets: [
    ['{', '}'],
    ['[', ']'],
    ['(', ')']
  ],
  autoClosingPairs: [
    { open: '{', close: '}' },
    { open: '[', close: ']' },
    { open: '(', close: ')' },
    { open: '"', close: '"' },
    { open: "'", close: "'" }
  ],
  surroundingPairs: [
    { open: '{', close: '}' },
    { open: '[', close: ']' },
    { open: '(', close: ')' },
    { open: '"', close: '"' },
    { open: "'", close: "'" }
  ],
  folding: {
    markers: {
      start: new RegExp('^\\s*//\\s*#region\\b'),
      end: new RegExp('^\\s*//\\s*#endregion\\b')
    }
  }
};

// HaasScript token provider
export const haasScriptTokenProvider: monaco.languages.IMonarchLanguage = {
  defaultToken: '',
  tokenPostfix: '.hss',

  keywords: [
    'if', 'else', 'elseif', 'endif', 'while', 'endwhile', 'for', 'endfor',
    'function', 'endfunction', 'return', 'break', 'continue', 'true', 'false',
    'and', 'or', 'not', 'null', 'undefined', 'var', 'const', 'let'
  ],

  builtinFunctions: [
    // Price functions
    'Open', 'High', 'Low', 'Close', 'Volume', 'Timestamp',
    
    // Technical indicators
    'RSI', 'MACD', 'EMA', 'SMA', 'BB', 'Stoch', 'ADX', 'ATR', 'CCI',
    'Williams', 'MFI', 'OBV', 'VWAP', 'Pivot', 'Fibonacci',
    
    // Math functions
    'Abs', 'Max', 'Min', 'Round', 'Floor', 'Ceil', 'Sqrt', 'Pow',
    'Sin', 'Cos', 'Tan', 'Log', 'Exp', 'Random',
    
    // Array functions
    'Length', 'Sum', 'Average', 'Highest', 'Lowest', 'CrossOver', 'CrossUnder',
    
    // Trading functions
    'Buy', 'Sell', 'ClosePosition', 'GetPosition', 'GetBalance', 'GetPrice',
    'SetStopLoss', 'SetTakeProfit', 'GetOrderStatus', 'CancelOrder',
    
    // Utility functions
    'Print', 'Alert', 'GetTime', 'FormatNumber', 'ToString', 'ToNumber'
  ],

  operators: [
    '=', '>', '<', '!', '~', '?', ':', '==', '<=', '>=', '!=',
    '&&', '||', '++', '--', '+', '-', '*', '/', '&', '|', '^', '%',
    '<<', '>>', '>>>', '+=', '-=', '*=', '/=', '&=', '|=', '^=',
    '%=', '<<=', '>>=', '>>>='
  ],

  symbols: /[=><!~?:&|+\-*\/\^%]+/,
  escapes: /\\(?:[abfnrtv\\"']|x[0-9A-Fa-f]{1,4}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})/,
  digits: /\d+(_+\d+)*/,
  octaldigits: /[0-7]+(_+[0-7]+)*/,
  binarydigits: /[0-1]+(_+[0-1]+)*/,
  hexdigits: /[[0-9a-fA-F]+(_+[0-9a-fA-F]+)*/,

  tokenizer: {
    root: [
      // Identifiers and keywords
      [/[a-zA-Z_$][\w$]*/, {
        cases: {
          '@keywords': 'keyword',
          '@builtinFunctions': 'predefined',
          '@default': 'identifier'
        }
      }],

      // Whitespace
      { include: '@whitespace' },

      // Numbers
      [/(@digits)[eE]([\-+]?(@digits))?[fFdD]?/, 'number.float'],
      [/(@digits)\.(@digits)([eE][\-+]?(@digits))?[fFdD]?/, 'number.float'],
      [/0[xX](@hexdigits)[Ll]?/, 'number.hex'],
      [/0(@octaldigits)[Ll]?/, 'number.octal'],
      [/0[bB](@binarydigits)[Ll]?/, 'number.binary'],
      [/(@digits)[fFdD]/, 'number.float'],
      [/(@digits)[lL]?/, 'number'],

      // Delimiter: after number because of .\d floats
      [/[;,.]/, 'delimiter'],

      // Strings
      [/"([^"\\]|\\.)*$/, 'string.invalid'],
      [/"/, 'string', '@string_double'],
      [/'([^'\\]|\\.)*$/, 'string.invalid'],
      [/'/, 'string', '@string_single'],

      // Characters
      [/'[^\\']'/, 'string'],
      [/(')(@escapes)(')/, ['string', 'string.escape', 'string']],
      [/'/, 'string.invalid'],

      // Operators
      [/@symbols/, {
        cases: {
          '@operators': 'operator',
          '@default': ''
        }
      }],

      // Brackets
      [/[{}()\[\]]/, '@brackets'],
    ],

    whitespace: [
      [/[ \t\r\n]+/, ''],
      [/\/\*\*(?!\/)/, 'comment.doc', '@jsdoc'],
      [/\/\*/, 'comment', '@comment'],
      [/\/\/.*$/, 'comment'],
    ],

    comment: [
      [/[^\/*]+/, 'comment'],
      [/\*\//, 'comment', '@pop'],
      [/[\/*]/, 'comment']
    ],

    jsdoc: [
      [/[^\/*]+/, 'comment.doc'],
      [/\*\//, 'comment.doc', '@pop'],
      [/[\/*]/, 'comment.doc']
    ],

    string_double: [
      [/[^\\"]+/, 'string'],
      [/@escapes/, 'string.escape'],
      [/\\./, 'string.escape.invalid'],
      [/"/, 'string', '@pop']
    ],

    string_single: [
      [/[^\\']+/, 'string'],
      [/@escapes/, 'string.escape'],
      [/\\./, 'string.escape.invalid'],
      [/'/, 'string', '@pop']
    ],
  },
};

// HaasScript completion provider
export const createHaasScriptCompletionProvider = (): monaco.languages.CompletionItemProvider => ({
  provideCompletionItems: (model, position) => {
    const word = model.getWordUntilPosition(position);
    const range = {
      startLineNumber: position.lineNumber,
      endLineNumber: position.lineNumber,
      startColumn: word.startColumn,
      endColumn: word.endColumn
    };

    const suggestions: monaco.languages.CompletionItem[] = [
      // Keywords
      ...haasScriptTokenProvider.keywords!.map((keyword: string) => ({
        label: keyword,
        kind: monaco.languages.CompletionItemKind.Keyword,
        insertText: keyword,
        range
      })),

      // Built-in functions
      ...haasScriptTokenProvider.builtinFunctions!.map((func: string) => ({
        label: func,
        kind: monaco.languages.CompletionItemKind.Function,
        insertText: `${func}()`,
        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
        range,
        documentation: `Built-in HaasScript function: ${func}`
      })),

      // Common patterns
      {
        label: 'if-else',
        kind: monaco.languages.CompletionItemKind.Snippet,
        insertText: [
          'if ${1:condition}',
          '\t${2:// code}',
          'else',
          '\t${3:// code}',
          'endif'
        ].join('\n'),
        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
        documentation: 'If-else statement',
        range
      },

      {
        label: 'for-loop',
        kind: monaco.languages.CompletionItemKind.Snippet,
        insertText: [
          'for ${1:i} = ${2:0} to ${3:10}',
          '\t${4:// code}',
          'endfor'
        ].join('\n'),
        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
        documentation: 'For loop',
        range
      },

      {
        label: 'function',
        kind: monaco.languages.CompletionItemKind.Snippet,
        insertText: [
          'function ${1:functionName}(${2:parameters})',
          '\t${3:// code}',
          '\treturn ${4:value}',
          'endfunction'
        ].join('\n'),
        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
        documentation: 'Function definition',
        range
      }
    ];

    return { suggestions };
  }
});

// Register HaasScript language
export const registerHaasScriptLanguage = () => {
  // Register the language
  monaco.languages.register({ id: 'haasscript' });

  // Set the language configuration
  monaco.languages.setLanguageConfiguration('haasscript', haasScriptLanguageConfig);

  // Set the token provider
  monaco.languages.setMonarchTokensProvider('haasscript', haasScriptTokenProvider);

  // Register completion provider
  monaco.languages.registerCompletionItemProvider('haasscript', createHaasScriptCompletionProvider());

  // Define theme
  monaco.editor.defineTheme('haasscript-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: '569cd6', fontStyle: 'bold' },
      { token: 'predefined', foreground: '4ec9b0' },
      { token: 'string', foreground: 'ce9178' },
      { token: 'number', foreground: 'b5cea8' },
      { token: 'comment', foreground: '6a9955', fontStyle: 'italic' },
      { token: 'comment.doc', foreground: '6a9955', fontStyle: 'italic' },
      { token: 'operator', foreground: 'd4d4d4' },
      { token: 'delimiter', foreground: 'd4d4d4' }
    ],
    colors: {
      'editor.background': '#1e1e1e',
      'editor.foreground': '#d4d4d4',
      'editorLineNumber.foreground': '#858585',
      'editorCursor.foreground': '#aeafad',
      'editor.selectionBackground': '#264f78',
      'editor.inactiveSelectionBackground': '#3a3d41'
    }
  });
};