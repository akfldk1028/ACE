import type { AssistantPreset, SkillDefinition } from './assistants.types'

// ---------- Skills (14) ----------

export const SKILLS: SkillDefinition[] = [
  {
    id: 'docx',
    name: 'DOCX',
    description: 'Word document creation, editing, tracked changes',
    icon: '\u{1F4C4}',
    triggers: ['docx', 'word', 'document', 'report'],
  },
  {
    id: 'pptx',
    name: 'PPTX',
    description: 'Presentation creation, editing, templates',
    icon: '\u{1F4CA}',
    triggers: ['pptx', 'powerpoint', 'presentation', 'slides'],
  },
  {
    id: 'xlsx',
    name: 'XLSX',
    description: 'Excel spreadsheet, charts, formulas',
    icon: '\u{1F4C8}',
    triggers: ['xlsx', 'excel', 'spreadsheet', 'data table'],
  },
  {
    id: 'pdf',
    name: 'PDF',
    description: 'PDF manipulation, form filling, extraction',
    icon: '\u{1F4D1}',
    triggers: ['pdf', 'form', 'extract text', 'merge pdf'],
  },
  {
    id: 'mermaid',
    name: 'Mermaid',
    description: 'Flowcharts, sequence, state, class, ER diagrams',
    icon: '\u{1F500}',
    triggers: ['mermaid', 'flowchart', 'diagram', 'sequence'],
  },
  {
    id: 'code-execution',
    name: 'Code Execution',
    description: 'Run Python/JS code in sandboxed environment',
    icon: '\u{1F4BB}',
    triggers: ['execute', 'run code', 'python', 'script'],
  },
  {
    id: 'web-search',
    name: 'Web Search',
    description: 'Search the web for real-time information',
    icon: '\u{1F50D}',
    triggers: ['search', 'browse', 'web', 'find online'],
  },
  {
    id: 'task-orchestrator',
    name: 'Task Orchestrator',
    description: 'Multi-step task planning and execution',
    icon: '\u{1F4CB}',
    triggers: ['plan', 'orchestrate', 'multi-step', 'workflow'],
  },
  // --- New skills ---
  {
    id: 'planning',
    name: 'File Planning',
    description: 'Manus-style 3-file persistent planning (task_plan / findings / progress)',
    icon: '\u{1F5C2}\uFE0F',
    triggers: ['plan', 'planning', 'organize', 'track'],
  },
  {
    id: 'ui-design',
    name: 'UI/UX Design',
    description: '57 styles, 95 palettes, typography DB for professional UI',
    icon: '\u{1F3A8}',
    triggers: ['design', 'ui', 'ux', 'layout', 'theme'],
  },
  {
    id: 'image-gen',
    name: 'Image Generation',
    description: 'AI image generation for assets and backgrounds',
    icon: '\u{1F5BC}\uFE0F',
    triggers: ['image', 'generate image', 'illustration'],
  },
  {
    id: 'recruiting',
    name: 'Recruiting',
    description: 'JD generation + multi-platform social publishing',
    icon: '\u{1F4BC}',
    triggers: ['job', 'recruit', 'hire', 'JD'],
  },
  {
    id: 'roleplay',
    name: 'Story Roleplay',
    description: 'Character cards, world info, immersive narrative',
    icon: '\u{1F3AD}',
    triggers: ['story', 'roleplay', 'character', 'fiction'],
  },
  {
    id: 'watermark-detect',
    name: 'Watermark Detection',
    description: 'AI watermark detection & removal from documents',
    icon: '\u{1F50E}',
    triggers: ['watermark', 'clean', 'detect'],
  },
]

// ---------- Assistant Presets (12) ----------

export const ASSISTANT_PRESETS: AssistantPreset[] = [
  // --- Existing 6 ---
  {
    id: 'cowork',
    avatar: '\u{1F916}',
    category: 'productivity',
    nameI18n: {
      'en-US': 'Cowork',
      'ko-KR': 'Cowork',
    },
    descriptionI18n: {
      'en-US': 'Autonomous task execution with file operations, document processing, and multi-step workflow planning.',
      'ko-KR': '\uD30C\uC77C \uC791\uC5C5, \uBB38\uC11C \uCC98\uB9AC \uBC0F \uB2E4\uB2E8\uACC4 \uC6CC\uD06C\uD50C\uB85C\uC6B0 \uACC4\uD68D\uC774 \uAC00\uB2A5\uD55C \uC790\uC728 \uC791\uC5C5 \uC2E4\uD589 \uC5B4\uC2DC\uC2A4\uD134\uD2B8.',
    },
    promptsI18n: {
      'en-US': ['Analyze the project structure', 'Create a project report', 'Automate the build process'],
      'ko-KR': ['\uD504\uB85C\uC81D\uD2B8 \uAD6C\uC870 \uBD84\uC11D', '\uD504\uB85C\uC81D\uD2B8 \uBCF4\uACE0\uC11C \uC791\uC131', '\uBE4C\uB4DC \uD504\uB85C\uC138\uC2A4 \uC790\uB3D9\uD654'],
    },
    skills: ['docx', 'pptx', 'xlsx', 'pdf', 'task-orchestrator'],
    pattern: 'RoundRobinGroupChat',
    recommendedModel: 'gpt-4o',
  },
  {
    id: 'code-assistant',
    avatar: '\u{1F4BB}',
    category: 'development',
    nameI18n: {
      'en-US': 'Code Assistant',
      'ko-KR': '\uCF54\uB4DC \uC5B4\uC2DC\uC2A4\uD134\uD2B8',
    },
    descriptionI18n: {
      'en-US': 'Write, review, debug, and test code with intelligent multi-agent collaboration.',
      'ko-KR': '\uC9C0\uB2A5\uD615 \uBA40\uD2F0 \uC5D0\uC774\uC804\uD2B8 \uD611\uC5C5\uC73C\uB85C \uCF54\uB4DC \uC791\uC131, \uB9AC\uBDF0, \uB514\uBC84\uAE45 \uBC0F \uD14C\uC2A4\uD2B8.',
    },
    promptsI18n: {
      'en-US': ['Review this code for bugs', 'Write unit tests for auth module', 'Refactor the database layer'],
      'ko-KR': ['\uC774 \uCF54\uB4DC\uC758 \uBC84\uADF8 \uAC80\uD1A0', '\uC778\uC99D \uBAA8\uB4C8 \uC720\uB2DB \uD14C\uC2A4\uD2B8 \uC791\uC131', '\uB370\uC774\uD130\uBCA0\uC774\uC2A4 \uB808\uC774\uC5B4 \uB9AC\uD329\uD1A0\uB9C1'],
    },
    skills: ['code-execution'],
    pattern: 'RoundRobinGroupChat',
    recommendedModel: 'claude-sonnet-4',
  },
  {
    id: 'research',
    avatar: '\u{1F52C}',
    category: 'development',
    nameI18n: {
      'en-US': 'Research Team',
      'ko-KR': '\uB9AC\uC11C\uCE58 \uD300',
    },
    descriptionI18n: {
      'en-US': 'Deep research with web search, analysis, and structured report generation.',
      'ko-KR': '\uC6F9 \uAC80\uC0C9, \uBD84\uC11D \uBC0F \uAD6C\uC870\uD654\uB41C \uBCF4\uACE0\uC11C \uC0DD\uC131\uC744 \uD1B5\uD55C \uC2EC\uCE35 \uC5F0\uAD6C.',
    },
    promptsI18n: {
      'en-US': ['Research latest AI trends', 'Compare React vs Vue in 2026', 'Analyze market for SaaS tools'],
      'ko-KR': ['\uCD5C\uC2E0 AI \uD2B8\uB80C\uB4DC \uB9AC\uC11C\uCE58', '2026\uB144 React vs Vue \uBE44\uAD50', 'SaaS \uB3C4\uAD6C \uC2DC\uC7A5 \uBD84\uC11D'],
    },
    skills: ['web-search', 'task-orchestrator'],
    pattern: 'SelectorGroupChat',
    recommendedModel: 'gpt-4o',
  },
  {
    id: 'presentation',
    avatar: '\u{1F4CA}',
    category: 'creative',
    nameI18n: {
      'en-US': 'Presentation Generator',
      'ko-KR': '\uD504\uB808\uC820\uD14C\uC774\uC158 \uC0DD\uC131\uAE30',
    },
    descriptionI18n: {
      'en-US': 'Create professional presentations with data visualization and consistent theming.',
      'ko-KR': '\uB370\uC774\uD130 \uC2DC\uAC01\uD654\uC640 \uC77C\uAD00\uB41C \uD14C\uB9C8\uB85C \uC804\uBB38\uC801\uC778 \uD504\uB808\uC820\uD14C\uC774\uC158\uC744 \uC0DD\uC131\uD569\uB2C8\uB2E4.',
    },
    promptsI18n: {
      'en-US': ['Create a slide deck about AI trends', 'Generate quarterly report presentation', 'Design a pitch deck'],
      'ko-KR': ['AI \uD2B8\uB80C\uB4DC \uC2AC\uB77C\uC774\uB4DC \uC791\uC131', '\uBD84\uAE30 \uBCF4\uACE0\uC11C \uD504\uB808\uC820\uD14C\uC774\uC158 \uC0DD\uC131', '\uD53C\uCE58 \uB371 \uB514\uC790\uC778'],
    },
    skills: ['pptx', 'mermaid', 'xlsx'],
    pattern: 'RoundRobinGroupChat',
    recommendedModel: 'gemini-2.5-pro',
  },
  {
    id: 'diagram',
    avatar: '\u{1F500}',
    category: 'creative',
    nameI18n: {
      'en-US': 'Diagram Builder',
      'ko-KR': '\uB2E4\uC774\uC5B4\uADF8\uB7A8 \uBE4C\uB354',
    },
    descriptionI18n: {
      'en-US': 'Create flowcharts, sequence diagrams, ER diagrams, and architecture visualizations.',
      'ko-KR': '\uD50C\uB85C\uC6B0\uCC28\uD2B8, \uC2DC\uD000\uC2A4 \uB2E4\uC774\uC5B4\uADF8\uB7A8, ER \uB2E4\uC774\uC5B4\uADF8\uB7A8 \uBC0F \uC544\uD0A4\uD14D\uCC98 \uC2DC\uAC01\uD654\uB97C \uC0DD\uC131\uD569\uB2C8\uB2E4.',
    },
    promptsI18n: {
      'en-US': ['Draw a user login flowchart', 'Create an API sequence diagram', 'Design a database ER diagram'],
      'ko-KR': ['\uC0AC\uC6A9\uC790 \uB85C\uADF8\uC778 \uD50C\uB85C\uC6B0\uCC28\uD2B8 \uADF8\uB9AC\uAE30', 'API \uC2DC\uD000\uC2A4 \uB2E4\uC774\uC5B4\uADF8\uB7A8 \uC0DD\uC131', '\uB370\uC774\uD130\uBCA0\uC774\uC2A4 ER \uB2E4\uC774\uC5B4\uADF8\uB7A8 \uC124\uACC4'],
    },
    skills: ['mermaid'],
    pattern: 'RoundRobinGroupChat',
    recommendedModel: 'claude-sonnet-4',
  },
  {
    id: 'data-analyst',
    avatar: '\u{1F4C8}',
    category: 'productivity',
    nameI18n: {
      'en-US': 'Data Analyst',
      'ko-KR': '\uB370\uC774\uD130 \uBD84\uC11D\uAC00',
    },
    descriptionI18n: {
      'en-US': 'Analyze data, create visualizations, and generate insights from spreadsheets and databases.',
      'ko-KR': '\uB370\uC774\uD130 \uBD84\uC11D, \uC2DC\uAC01\uD654 \uC0DD\uC131, \uC2A4\uD504\uB808\uB4DC\uC2DC\uD2B8 \uBC0F \uB370\uC774\uD130\uBCA0\uC774\uC2A4\uC5D0\uC11C \uC778\uC0AC\uC774\uD2B8\uB97C \uB3C4\uCD9C\uD569\uB2C8\uB2E4.',
    },
    promptsI18n: {
      'en-US': ['Analyze this CSV data', 'Create a sales dashboard', 'Find patterns in user behavior'],
      'ko-KR': ['\uC774 CSV \uB370\uC774\uD130 \uBD84\uC11D', '\uB9E4\uCD9C \uB300\uC2DC\uBCF4\uB4DC \uC0DD\uC131', '\uC0AC\uC6A9\uC790 \uD589\uB3D9 \uD328\uD134 \uBC1C\uACAC'],
    },
    skills: ['xlsx', 'code-execution'],
    pattern: 'RoundRobinGroupChat',
    recommendedModel: 'gpt-4o',
  },

  // --- New 6 ---
  {
    id: 'planning',
    avatar: '\u{1F4CB}',
    category: 'productivity',
    nameI18n: {
      'en-US': 'Planning & Files',
      'ko-KR': '\uACC4\uD68D & \uD30C\uC77C',
    },
    descriptionI18n: {
      'en-US': 'Manus-style 3-file persistent planning: task_plan.md, findings.md, progress.md for complex multi-step tasks.',
      'ko-KR': 'Manus \uC2A4\uD0C0\uC77C 3-\uD30C\uC77C \uC601\uAD6C \uACC4\uD68D: \uBCF5\uC7A1\uD55C \uB2E4\uB2E8\uACC4 \uC791\uC5C5\uC744 \uC704\uD55C task_plan / findings / progress \uD30C\uC77C.',
    },
    promptsI18n: {
      'en-US': ['Plan a complex migration project', 'Organize research into structured files', 'Track multi-phase deployment'],
      'ko-KR': ['\uBCF5\uC7A1\uD55C \uB9C8\uC774\uADF8\uB808\uC774\uC158 \uD504\uB85C\uC81D\uD2B8 \uACC4\uD68D', '\uB9AC\uC11C\uCE58\uB97C \uAD6C\uC870\uD654\uB41C \uD30C\uC77C\uB85C \uC815\uB9AC', '\uB2E4\uB2E8\uACC4 \uBC30\uD3EC \uCD94\uC801'],
    },
    skills: ['planning', 'task-orchestrator', 'docx'],
    pattern: 'RoundRobinGroupChat',
    recommendedModel: 'claude-sonnet-4',
    systemPromptI18n: {
      'en-US': 'You use the Manus-style 3-file planning pattern. For every complex task, create THREE files: task_plan.md (phases & progress), findings.md (research & discoveries), progress.md (session log & test results). Rules: (1) Create plan files FIRST before any work. (2) Re-read task_plan.md before major decisions. (3) Update status after every phase. (4) Log ALL errors. (5) Never repeat failed actions. (6) After every 2 search/view operations, save findings immediately.',
      'ko-KR': 'Manus \uC2A4\uD0C0\uC77C 3-\uD30C\uC77C \uACC4\uD68D \uD328\uD134\uC744 \uC0AC\uC6A9\uD569\uB2C8\uB2E4. \uBCF5\uC7A1\uD55C \uC791\uC5C5\uB9C8\uB2E4 3\uAC1C \uD30C\uC77C\uC744 \uC0DD\uC131\uD569\uB2C8\uB2E4: task_plan.md (\uB2E8\uACC4 & \uC9C4\uD589), findings.md (\uC5F0\uAD6C & \uBC1C\uACAC), progress.md (\uC138\uC158 \uB85C\uADF8 & \uD14C\uC2A4\uD2B8 \uACB0\uACFC). \uADDC\uCE59: (1) \uC791\uC5C5 \uC804 \uACC4\uD68D \uD30C\uC77C \uBA3C\uC800 \uC0DD\uC131. (2) \uC911\uC694 \uACB0\uC815 \uC804 task_plan.md \uC7AC\uD655\uC778. (3) \uB2E8\uACC4\uB9C8\uB2E4 \uC0C1\uD0DC \uC5C5\uB370\uC774\uD2B8. (4) \uBAA8\uB4E0 \uC624\uB958 \uAE30\uB85D. (5) \uC2E4\uD328\uD55C \uC791\uC5C5 \uBC18\uBCF5 \uAE08\uC9C0. (6) \uAC80\uC0C9/\uC870\uD68C 2\uD68C \uD6C4 \uBC1C\uACAC \uC989\uC2DC \uC800\uC7A5.',
    },
  },
  {
    id: 'ui-designer',
    avatar: '\u{1F3A8}',
    category: 'creative',
    nameI18n: {
      'en-US': 'UI/UX Designer',
      'ko-KR': 'UI/UX \uB514\uC790\uC774\uB108',
    },
    descriptionI18n: {
      'en-US': 'Professional design intelligence with 57 UI styles, 95 color palettes, and comprehensive UX guidelines.',
      'ko-KR': '57\uAC1C UI \uC2A4\uD0C0\uC77C, 95\uAC1C \uCEEC\uB7EC \uD314\uB808\uD2B8, \uD3EC\uAD04\uC801 UX \uAC00\uC774\uB4DC\uB77C\uC778\uC744 \uAC16\uCD98 \uC804\uBB38 \uB514\uC790\uC778 \uC5B4\uC2DC\uC2A4\uD134\uD2B8.',
    },
    promptsI18n: {
      'en-US': ['Design a SaaS landing page', 'Create a dark-mode dashboard UI', 'Build a glassmorphism card component'],
      'ko-KR': ['SaaS \uB79C\uB529 \uD398\uC774\uC9C0 \uB514\uC790\uC778', '\uB2E4\uD06C\uBAA8\uB4DC \uB300\uC2DC\uBCF4\uB4DC UI \uC0DD\uC131', '\uAE00\uB798\uC2A4\uBAA8\uD53C\uC998 \uCE74\uB4DC \uCEF4\uD3EC\uB10C\uD2B8 \uC81C\uC791'],
    },
    skills: ['ui-design', 'image-gen', 'code-execution'],
    pattern: 'SelectorGroupChat',
    recommendedModel: 'claude-sonnet-4',
    systemPromptI18n: {
      'en-US': 'You are a specialized UI/UX design assistant. Professional UI Rules: (1) No emoji icons - use SVG icons (Heroicons, Lucide). (2) Stable hover states - use color/opacity transitions, not scale transforms. (3) cursor-pointer on all clickable elements. (4) Light/dark mode contrast - bg-white/80 in light, sufficient text contrast (4.5:1). (5) Consistent spacing and max-width. Pre-delivery checklist: verify no emojis as icons, hover states, focus states, responsive at 320/768/1024/1440px, accessibility (alt text, labels, prefers-reduced-motion).',
      'ko-KR': 'UI/UX \uB514\uC790\uC778 \uC804\uBB38 \uC5B4\uC2DC\uC2A4\uD134\uD2B8\uC785\uB2C8\uB2E4. \uD504\uB85C UI \uADDC\uCE59: (1) \uC774\uBAA8\uC9C0 \uC544\uC774\uCF58 \uAE08\uC9C0 - SVG \uC544\uC774\uCF58 \uC0AC\uC6A9 (Heroicons, Lucide). (2) \uC548\uC815\uC801 \uD638\uBC84 - \uC0C9\uC0C1/\uD22C\uBA85\uB3C4 \uC804\uD658 \uC0AC\uC6A9. (3) \uD074\uB9AD \uAC00\uB2A5\uD55C \uC694\uC18C\uC5D0 cursor-pointer. (4) \uB77C\uC774\uD2B8/\uB2E4\uD06C \uBAA8\uB4DC \uB300\uBE44 - \uCDA9\uBD84\uD55C \uD14D\uC2A4\uD2B8 \uB300\uBE44 (4.5:1). (5) \uC77C\uAD00\uB41C \uC5EC\uBC31\uACFC max-width. \uBC30\uD3EC \uC804 \uCCB4\uD06C\uB9AC\uC2A4\uD2B8: \uC774\uBAA8\uC9C0 \uC544\uC774\uCF58, \uD638\uBC84, \uD3EC\uCEE4\uC2A4, \uBC18\uC751\uD615 320/768/1024/1440px, \uC811\uADFC\uC131 \uD655\uC778.',
    },
  },
  {
    id: 'pdf-converter',
    avatar: '\u{1F4D1}',
    category: 'development',
    nameI18n: {
      'en-US': 'PDF to PPT',
      'ko-KR': 'PDF to PPT',
    },
    descriptionI18n: {
      'en-US': 'Convert PDF documents to PowerPoint with layout preservation and watermark removal.',
      'ko-KR': 'PDF \uBB38\uC11C\uB97C \uB808\uC774\uC544\uC6C3 \uBCF4\uC874 \uBC0F \uC6CC\uD130\uB9C8\uD06C \uC81C\uAC70\uB85C PowerPoint\uB85C \uBCC0\uD658\uD569\uB2C8\uB2E4.',
    },
    promptsI18n: {
      'en-US': ['Convert this PDF to slides', 'Extract text and images from PDF', 'Remove watermarks and create PPT'],
      'ko-KR': ['\uC774 PDF\uB97C \uC2AC\uB77C\uC774\uB4DC\uB85C \uBCC0\uD658', 'PDF\uC5D0\uC11C \uD14D\uC2A4\uD2B8\uC640 \uC774\uBBF8\uC9C0 \uCD94\uCD9C', '\uC6CC\uD130\uB9C8\uD06C \uC81C\uAC70 \uD6C4 PPT \uC0DD\uC131'],
    },
    skills: ['pdf', 'pptx', 'watermark-detect'],
    pattern: 'RoundRobinGroupChat',
    recommendedModel: 'gpt-4o',
    systemPromptI18n: {
      'en-US': 'You convert PDF files to PowerPoint presentations. Workflow: (1) Analyze PDF structure, extract text, images, and layout. (2) Identify and remove watermarks (NotebookLM signatures, semi-transparent overlays, diagonal text). (3) Generate PPT preserving text hierarchy, image positions, and aspect ratios. (4) Use clean, professional slide templates with readable font sizes.',
      'ko-KR': 'PDF \uD30C\uC77C\uC744 PowerPoint \uD504\uB808\uC820\uD14C\uC774\uC158\uC73C\uB85C \uBCC0\uD658\uD569\uB2C8\uB2E4. \uC6CC\uD06C\uD50C\uB85C\uC6B0: (1) PDF \uAD6C\uC870 \uBD84\uC11D, \uD14D\uC2A4\uD2B8/\uC774\uBBF8\uC9C0/\uB808\uC774\uC544\uC6C3 \uCD94\uCD9C. (2) \uC6CC\uD130\uB9C8\uD06C \uC2DD\uBCC4 \uBC0F \uC81C\uAC70. (3) \uD14D\uC2A4\uD2B8 \uACC4\uCE35, \uC774\uBBF8\uC9C0 \uC704\uCE58, \uBE44\uC728 \uBCF4\uC874\uD558\uC5EC PPT \uC0DD\uC131. (4) \uAE54\uB054\uD558\uACE0 \uC804\uBB38\uC801\uC778 \uC2AC\uB77C\uC774\uB4DC \uD15C\uD50C\uB9BF \uC0AC\uC6A9.',
    },
  },
  {
    id: 'pptx-creator',
    avatar: '\u{1F4CA}',
    category: 'creative',
    nameI18n: {
      'en-US': 'PPTX Creator',
      'ko-KR': 'PPTX \uC81C\uC791\uAE30',
    },
    descriptionI18n: {
      'en-US': 'Generate local PowerPoint files via pptxgenjs JSON slide spec with visual style templates.',
      'ko-KR': 'pptxgenjs JSON \uC2AC\uB77C\uC774\uB4DC \uC2A4\uD399\uACFC \uBE44\uC8FC\uC5BC \uC2A4\uD0C0\uC77C \uD15C\uD50C\uB9BF\uC73C\uB85C \uB85C\uCEEC PowerPoint \uD30C\uC77C \uC0DD\uC131.',
    },
    promptsI18n: {
      'en-US': ['Create a 10-slide pitch deck', 'Generate quarterly report slides', 'Build a product launch presentation'],
      'ko-KR': ['10\uC7A5 \uD53C\uCE58 \uB371 \uC0DD\uC131', '\uBD84\uAE30 \uBCF4\uACE0\uC11C \uC2AC\uB77C\uC774\uB4DC \uC0DD\uC131', '\uC81C\uD488 \uCD9C\uC2DC \uD504\uB808\uC820\uD14C\uC774\uC158 \uC81C\uC791'],
    },
    skills: ['pptx', 'image-gen'],
    pattern: 'SelectorGroupChat',
    recommendedModel: 'gemini-2.5-pro',
    systemPromptI18n: {
      'en-US': 'You generate PPTX files using pptxgenjs. Output: slides.json (deck spec) + generate-pptx.js (Node script). Slide types: title, bullets, two-column, image, quote, section, summary. Always pick a visual template (Modern Gradient, Editorial, Neon Tech, etc.). Generate background images for consistent theming. Use LAYOUT_WIDE by default. After writing files, execute: node generate-pptx.js.',
      'ko-KR': 'pptxgenjs\uB97C \uC0AC\uC6A9\uD558\uC5EC PPTX \uD30C\uC77C\uC744 \uC0DD\uC131\uD569\uB2C8\uB2E4. \uCD9C\uB825: slides.json (\uB371 \uC2A4\uD399) + generate-pptx.js (Node \uC2A4\uD06C\uB9BD\uD2B8). \uC2AC\uB77C\uC774\uB4DC \uC720\uD615: title, bullets, two-column, image, quote, section, summary. \uD56D\uC0C1 \uBE44\uC8FC\uC5BC \uD15C\uD50C\uB9BF \uC120\uD0DD. \uC77C\uAD00\uB41C \uD14C\uB9C8\uB97C \uC704\uD55C \uBC30\uACBD \uC774\uBBF8\uC9C0 \uC0DD\uC131. \uAE30\uBCF8 LAYOUT_WIDE \uC0AC\uC6A9.',
    },
  },
  {
    id: 'recruiter',
    avatar: '\u{1F4BC}',
    category: 'productivity',
    nameI18n: {
      'en-US': 'Job Publisher',
      'ko-KR': '\uCC44\uC6A9 \uD37C\uBE14\uB9AC\uC154',
    },
    descriptionI18n: {
      'en-US': 'Generate complete JDs with platform-specific social copy for X, LinkedIn, and more.',
      'ko-KR': 'X, LinkedIn \uB4F1 \uD50C\uB7AB\uD3FC\uBCC4 \uC18C\uC15C \uCE74\uD53C\uC640 \uD568\uAED8 \uC644\uC804\uD55C JD\uB97C \uC0DD\uC131\uD569\uB2C8\uB2E4.',
    },
    promptsI18n: {
      'en-US': ['Create a JD for a senior engineer', 'Generate LinkedIn post for hiring', 'Publish job opening on X and LinkedIn'],
      'ko-KR': ['\uC2DC\uB2C8\uC5B4 \uC5D4\uC9C0\uB2C8\uC5B4 JD \uC0DD\uC131', 'LinkedIn \uCC44\uC6A9 \uD3EC\uC2A4\uD2B8 \uC0DD\uC131', 'X\uC640 LinkedIn\uC5D0 \uCC44\uC6A9 \uACF5\uACE0 \uBC1C\uD589'],
    },
    skills: ['recruiting', 'image-gen'],
    pattern: 'SelectorGroupChat',
    recommendedModel: 'gpt-4o',
    systemPromptI18n: {
      'en-US': 'You turn hiring requests into complete JDs and social copy. Output order: (1) Full JD with role title, responsibilities, requirements, nice-to-haves, and application method. (2) Platform-specific copy: X (280 chars), LinkedIn (professional bullets), Redbook (warm tone + hashtags). (3) Cover image + detail image specs (1080x1350). Rules: Avoid biased language. Emphasize role value and growth. Ensure application method is present.',
      'ko-KR': '\uCC44\uC6A9 \uC694\uCCAD\uC744 \uC644\uC804\uD55C JD\uC640 \uC18C\uC15C \uCE74\uD53C\uB85C \uBCC0\uD658\uD569\uB2C8\uB2E4. \uCD9C\uB825 \uC21C\uC11C: (1) \uC5ED\uD560, \uCC45\uC784, \uC694\uAD6C\uC0AC\uD56D, \uC6B0\uB300\uC0AC\uD56D, \uC9C0\uC6D0 \uBC29\uBC95\uC774 \uD3EC\uD568\uB41C \uC804\uCCB4 JD. (2) \uD50C\uB7AB\uD3FC\uBCC4 \uCE74\uD53C: X (280\uC790), LinkedIn (\uC804\uBB38\uC801 \uBD88\uB9BF), Redbook (\uB530\uB73B\uD55C \uD1A4 + \uD574\uC2DC\uD0DC\uADF8). (3) \uCEE4\uBC84 + \uC0C1\uC138 \uC774\uBBF8\uC9C0 \uC2A4\uD399. \uADDC\uCE59: \uD3B8\uD5A5\uB41C \uC5B8\uC5B4 \uAE08\uC9C0. \uC5ED\uD560 \uAC00\uCE58\uC640 \uC131\uC7A5 \uAC15\uC870.',
    },
  },
  {
    id: 'storyteller',
    avatar: '\u270D\uFE0F',
    category: 'creative',
    nameI18n: {
      'en-US': 'Story & Roleplay',
      'ko-KR': '\uC2A4\uD1A0\uB9AC & \uB864\uD50C\uB808\uC774',
    },
    descriptionI18n: {
      'en-US': 'Immersive narrative experiences with SillyTavern character cards, world info, and dynamic storytelling.',
      'ko-KR': 'SillyTavern \uCE90\uB9AD\uD130 \uCE74\uB4DC, \uC6D4\uB4DC \uC778\uD3EC, \uB2E4\uC774\uB098\uBBF9 \uC2A4\uD1A0\uB9AC\uD154\uB9C1\uC73C\uB85C \uBAB0\uC785\uD615 \uB0B4\uB7EC\uD2F0\uBE0C \uACBD\uD5D8.',
    },
    promptsI18n: {
      'en-US': ['Create a fantasy adventure character', 'Start a sci-fi roleplay scenario', 'Build a mystery story world'],
      'ko-KR': ['\uD310\uD0C0\uC9C0 \uBAA8\uD5D8 \uCE90\uB9AD\uD130 \uC0DD\uC131', 'SF \uB864\uD50C\uB808\uC774 \uC2DC\uB098\uB9AC\uC624 \uC2DC\uC791', '\uBBF8\uC2A4\uD130\uB9AC \uC2A4\uD1A0\uB9AC \uC138\uACC4\uAD00 \uAD6C\uCD95'],
    },
    skills: ['roleplay'],
    pattern: 'Swarm',
    recommendedModel: 'claude-sonnet-4',
    systemPromptI18n: {
      'en-US': 'You are an immersive story roleplay assistant compatible with SillyTavern character card format. Features: (1) Maintain character personality, speech patterns, and motivations. (2) Use vivid descriptions, dialogue, and actions. (3) Support PNG/WebP/JSON character cards and world info files. (4) Dynamically update world-info.json as the story develops. Response format: Actions in third person (italics), dialogue in quotes, scene-setting for context. Three start modes: natural language character creation, image card parsing, or workspace folder auto-detection.',
      'ko-KR': 'SillyTavern \uCE90\uB9AD\uD130 \uCE74\uB4DC \uD3EC\uB9F7\uACFC \uD638\uD658\uB418\uB294 \uBAB0\uC785\uD615 \uC2A4\uD1A0\uB9AC \uB864\uD50C\uB808\uC774 \uC5B4\uC2DC\uC2A4\uD134\uD2B8\uC785\uB2C8\uB2E4. \uAE30\uB2A5: (1) \uCE90\uB9AD\uD130 \uC131\uACA9, \uB9D0\uD22C, \uB3D9\uAE30 \uC720\uC9C0. (2) \uC0DD\uB3D9\uD55C \uBB18\uC0AC, \uB300\uD654, \uD589\uB3D9 \uC0AC\uC6A9. (3) PNG/WebP/JSON \uCE90\uB9AD\uD130 \uCE74\uB4DC\uC640 \uC6D4\uB4DC \uC778\uD3EC \uC9C0\uC6D0. (4) \uC2A4\uD1A0\uB9AC \uC804\uAC1C\uC5D0 \uB530\uB77C world-info.json \uB3D9\uC801 \uC5C5\uB370\uC774\uD2B8. \uC751\uB2F5 \uD615\uC2DD: \uD589\uB3D9\uC740 3\uC778\uCE6D(\uC774\uD0E4\uB9AD), \uB300\uD654\uB294 \uB530\uC634\uD45C, \uC7A5\uBA74 \uC124\uC815\uC740 \uBB38\uB9E5 \uC81C\uACF5.',
    },
  },
]
