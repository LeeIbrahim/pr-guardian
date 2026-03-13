import { useState, useEffect, useRef } from 'react';
import Select from 'react-select';
import type { StylesConfig, GroupBase } from 'react-select';

// TODO: handle google authentication.

// TODO: Fix google explorer. I think this is a permission issue in cloud.console.

interface MyOption {
  value: string;
  label: string;
}

interface FileEntry {
  name: string;
  startLine: number;
  endLine: number;
}

declare global {
  interface Window {
    google: any;
    gapi: any;
  }
}

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
const CLIENT_API_KEY = import.meta.env.VITE_GOOGLE_CLIENT_API_KEY || ''; 
const SCOPES = "https://www.googleapis.com/auth/drive.readonly";
const BACKEND = import.meta.env.VITE_BACKEND_URL;
const GITHUB_API = "https://github.com";

function App() {
  const [models, setModels] = useState<MyOption[]>([]);
  const [selectedOptions, setSelectedOptions] = useState<MyOption[]>([]);
  const [code, setCode] = useState<string>('');
  const [results, setResults] = useState<Record<string, string>>({});
  const [loadingModels, setLoadingModels] = useState<Set<string>>(new Set());
  const [fileList, setFileList] = useState<FileEntry[]>([]);
  const [repoUrl, setRepoUrl] = useState<string>('');
  const [stagedFiles, setStagedFiles] = useState<{path: string, url: string}[]>([]);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Temporary fix to handle the spin down of back end and needing to load it up.
  useEffect(() => {
    const loadModels = async () => {
      setModels(Object.entries(import.meta.env.VITE_AVAILABLE_MODELS).map(([name, model_id]) => ({
          label: name,
          value: model_id
      })));
    };
    loadModels();

    // Loads backend into memory of render (deployment site) by spinning it up.
    fetch(BACKEND, { method: 'GET'}).then(() => console.log("Loaded backend"));
  }, []);

  // Update file sidebar and calculate boundaries whenever code changes
  useEffect(() => {
    const lines = code.split('\n');
    const files: FileEntry[] = [];
    
    lines.forEach((line, index) => {
      if (line.startsWith('--- File: ') || line.startsWith('--- Google Drive: ')) {
        const name = line.replace(/--- (File|Google Drive): (.*) ---/, '$2');
        files.push({ name, startLine: index, endLine: -1 });
      }
    });

    // Determine where each file ends
    files.forEach((file, i) => {
      if (i < files.length - 1) {
        file.endLine = files[i + 1].startLine - 1;
      } else {
        file.endLine = lines.length - 1;
      }
    });

    setFileList(files);
  }, [code]);

  const removeFile = (fileToRemove: FileEntry) => {
    const lines = code.split('\n');
    // Filter out lines that belong to this file range
    const newLines = lines.filter((_, index) => index < fileToRemove.startLine || index > fileToRemove.endLine);
    setCode(newLines.join('\n').trim());
  };

  const scrollToSection = (lineIndex: number) => {
    if (!textareaRef.current) return;
    const lineHeight = 21; 
    textareaRef.current.scrollTop = lineIndex * lineHeight;
    textareaRef.current.focus();
  };

  const clearAll = () => {
    setCode('');
    setResults({});
    setLoadingModels(new Set());
  };

  const handleDrivePicker = () => {
    if (!window.google || !window.google.accounts) return;
    const tokenClient = window.google.accounts.oauth2.initTokenClient({
      client_id: CLIENT_ID,
      scope: SCOPES,
      callback: async (response: any) => {
        if (response.access_token) {
          openPicker(response.access_token);
        }
      },
    });
    tokenClient.requestAccessToken();
  };

  const openPicker = (token: string) => {
    const picker = new window.google.picker.PickerBuilder()
      .addView(window.google.picker.ViewId.DOCS)
      .setOAuthToken(token)
      .setDeveloperKey(CLIENT_API_KEY)
      .setCallback(async (data: any) => {
        if (data.action === window.google.picker.Action.PICKED) {
          const file = data.docs[0];
          await fetchDriveFile(file.id, file.name, token);
        }
      })
      .build();
    picker.setVisible(true);
  };

  const fetchDriveFile = async (fileId: string, fileName: string, token: string) => {
    const response = await fetch(
      `https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    const content = await response.text();
    setCode(prev => {
      const separator = prev.trim() ? "\n\n" : "";
      return `${prev}${separator}--- Google Drive: ${fileName} ---\n${content}`;
    });
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;
    const results = await Promise.all(Array.from(files).map(file => {
      return new Promise<{name: string, content: string}>(resolve => {
        const reader = new FileReader();
        reader.onload = (e) => resolve({ name: file.name, content: e.target?.result as string });
        reader.readAsText(file);
      });
    }));
    setCode(prev => {
      let newCode = prev;
      results.forEach(f => {
        const sep = newCode.trim() ? "\n\n" : "";
        newCode += `${sep}--- File: ${f.name} ---\n${f.content}`;
      });
      return newCode;
    });
    event.target.value = '';
  };

  const handleAudit = async () => {
    if (!code || selectedOptions.length === 0) return;
    const currentlyLoading = new Set(selectedOptions.map(o => o.value));
    setLoadingModels(currentlyLoading);
    setResults({});

    try {
      const response = await fetch(`${BACKEND}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          model_names: selectedOptions.map(opt => opt.value),
          user_message: ""
        }),
      });

      if (!response.ok) throw new Error(`Server Error: ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunks = decoder.decode(value).split('\n\n');
        chunks.forEach(chunk => {
          if (chunk.startsWith('data: ')) {
            try {
              const data = JSON.parse(chunk.replace('data: ', ''));
              setResults(prev => ({ ...prev, [data.model]: data.review }));
              setLoadingModels(prev => {
                const next = new Set(prev);
                next.delete(data.model);
                return next;
              });
            } catch (e) { console.error("Parse error", e); }
          }
        });
      }
    } catch (error: any) {
      const errorMsg = `Error: ${error.message}`;
      const errResults: Record<string, string> = {};
      selectedOptions.forEach(o => errResults[o.value] = errorMsg);
      setResults(errResults);
      setLoadingModels(new Set());
    }
  };

  const handleGitHubPull = async () => {
    if (!repoUrl) return;

    try {
      // Parse owner and repo.
      const urlParts = repoUrl.replace('https://github.com/', '').split('/');
      
      if (urlParts.length < 2) throw new Error("Invalid GitHub URL");

      const [owner, repo] = urlParts;

      const repoRes = await fetch(`${GITHUB_API}/repos/${owner}/${repo}`);
      const repoData = await repoRes.json();
      // TODO: implement user selection of branches.
      const branch = repoData.default_branch;

      const treeRes = await fetch(`${GITHUB_API}/repos/${owner}/${repo}/git/trees/${branch}?recursive=1`);
      const treeData = await treeRes.json();

      const codeFiles = treeData.tree
        .filter((f: any) => f.type === 'blob' && /\.(ts|tsx|js|jsx|py|cs|java|cpp|go|rs)$/.test(f.path))
        .map((f: any) => ({
          path: f.path,
          url: `${GITHUB_API}/repos/${owner}/${repo}/contents/${f.path}?ref=${branch}`
        }));

      setStagedFiles(codeFiles);

    } catch (error: any) {
      alert("GutHub Pull Failed:" + error.message);
    }
  }

  const importStagedFile = async (file: {path: string, url: string}) => {
    try {
      const res = await fetch(file.url);
      const data = await res.json();
      const content = atob(data.content.replace(/\n/g, ''));

      setCode(prev => {
        const sep = prev.trim() ? "\n\n" : "";
        return `${prev}${sep}--- File: ${file.path} ---\n${content}`;
      });

      setStagedFiles(prev => prev.filter(f => f.path !== file.path));

    } catch (error: any) {
      alert("Import Failed:" + error.message);
      console.error(error);
    }
  };

  const customStyles: StylesConfig<MyOption, true, GroupBase<MyOption>> = {
    control: (base) => ({
      ...base,
      backgroundColor: '#2c2c2c',
      borderColor: '#444',
      color: '#fff'
    }),
    menu: (base) => ({ ...base, backgroundColor: '#2c2c2c' }),
    option: (base, state) => ({
      ...base,
      backgroundColor: state.isFocused ? '#444' : '#2c2c2c',
      color: '#fff'
    }),
    multiValue: (base) => ({ ...base, backgroundColor: '#444' }),
    multiValueLabel: (base) => ({ ...base, color: '#fff' }),
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1 className="logo">PR Guardian</h1>
        <div className="controls">
          <Select
            isMulti
            options={models}
            styles={customStyles}
            value={selectedOptions}
            onChange={(val) => setSelectedOptions(val ? [...val] : [])}
            placeholder="Select models..."
          />
          <button className="secondary-btn" onClick={clearAll}>Clear All</button>
        </div>
      </header>

      <main className="workspace">
        <div className="editor-container">
          <textarea
            ref={textareaRef}
            className="code-editor"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Paste code or use actions below..."
          />
          <div className="editor-footer">
            <label className="footer-btn action-btn">
              📁 Upload Files
              <input type="file" hidden multiple onChange={handleFileUpload} />
            </label>
            <button className="footer-btn action-btn" onClick={handleDrivePicker}>
              ☁️ Google Drive
            </button>
            <button 
              className="footer-btn primary-btn" 
              onClick={handleAudit} 
              disabled={loadingModels.size > 0}
            >
              {loadingModels.size > 0 ? "Analyzing..." : "🚀 Run 5-Pillar Audit"}
            </button>
          </div>
        </div>

        <aside className="sidebar">
          <h3>Project Files</h3>
          <div className="file-list">
            {fileList.length === 0 && <p className="empty-msg">No files detected</p>}
            {fileList.map((file, i) => (
              <div key={i} className="file-item">
                <span className="file-link" onClick={() => scrollToSection(file.startLine)}>
                  📄 {file.name}
                </span>
                <button className="remove-file-btn" onClick={() => removeFile(file)}>×</button>
              </div>
            ))}
          </div>
        </aside>
      </main>

      <footer className="results-grid" style={{ gridTemplateColumns: `repeat(${selectedOptions.length || 1}, 1fr)` }}>
        {selectedOptions.map(option => (
          <div key={option.value} className="result-card">
            <h4>{option.label}</h4>
            <div className="result-content">
              {loadingModels.has(option.value) ? (
                <div className="loader-box"><div className="spinner"></div><p>Auditing...</p></div>
              ) : (
                <pre>{results[option.value] || "Ready for audit"}</pre>
              )}
            </div>
          </div>
        ))}
      </footer>
    </div>
  );
}

export default App;