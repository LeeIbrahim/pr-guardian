import { useState, useEffect } from 'react';
import Select from 'react-select';
import type { StylesConfig, GroupBase } from 'react-select';

interface MyOption {
  value: string;
  label: string;
}

function App() {
  const [models, setModels] = useState<MyOption[]>([]);
  const [selectedOptions, setSelectedOptions] = useState<MyOption[]>([]);
  const [code, setCode] = useState<string>('');
  const [results, setResults] = useState<Record<string, string>>({});

  const customStyles: StylesConfig<MyOption, true, GroupBase<MyOption>> = {
    control: (base) => ({
      ...base,
      backgroundColor: '#2c2c2c',
      borderColor: '#444',
      minHeight: '40px',
      boxShadow: 'none',
      '&:hover': { borderColor: '#666' }
    }),
    multiValue: (base) => ({
      ...base,
      backgroundColor: '#444',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
    }),
    multiValueLabel: (base) => ({
      ...base,
      color: '#ffffff',
      padding: '3px 6px',
      fontSize: '14px',
      fontWeight: '600',
    }),
    multiValueRemove: (base) => ({
      ...base,
      color: '#ffffff',
      '&:hover': {
        backgroundColor: '#ff4444',
        color: 'white',
      },
    }),
    placeholder: (base) => ({
      ...base,
      color: '#aaaaaa',
    }),
    input: (base) => ({
      ...base,
      color: '#ffffff',
    }),
    menu: (base) => ({
      ...base,
      backgroundColor: '#2c2c2c',
      zIndex: 9999,
      border: '1px solid #444',
    }),
    option: (base, state) => ({
      ...base,
      backgroundColor: state.isFocused ? '#444' : '#2c2c2c',
      color: '#ffffff',
      cursor: 'pointer',
      padding: '10px',
    }),
  };

  const fetchModels = async (): Promise<void> => {
    try {
      const response = await fetch('https://127.0.0.1:8000/models');
      if (!response.ok) throw new Error('Network response was not ok');
      
      const data: MyOption[] = await response.json();

      setModels(data);

    } catch (error) {
      if (error instanceof Error) {
        console.error('Error fetching models:', error.message);
      }
    }
  };
  const handleAudit = async (): Promise<void> => {
    if (!code || selectedOptions.length === 0) {
      alert('Please select at least one model and input code from at least one source.');
      return;
    }

    const initialResults: Record<string, string> = {};
    selectedOptions.forEach(opt => initialResults[opt.value] = "");
    setResults(initialResults);

    const response = await fetch('https://127.0.0.1:8000/review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: code,
        model_names: selectedOptions.map(opt => opt.value),
        // this is for when I get the user message box into the code again.
        user_message: ""
      }),
    });

    if (!response.body) return;

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    
    let partialChunk = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = partialChunk + decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      partialChunk = lines.pop() || '';

      lines.forEach(line => {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith('data: ')) {
          try {
            const joinStr = trimmedLine.replace('data: ', '')
            const data = JSON.parse(joinStr);
            console.log("Received Data:", data);
            console.log("Received Model:", data.model, "Expected Keys:", Object.keys(results));
            setResults(prev => ({
              ...prev,
              [data.model]: (prev[data.model] || "") + data.review
            }));
          } catch (err) {
            console.error('Error parsing chunk:', err);
            partialChunk = line + partialChunk;
          }
        }
      });
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const fileArray = Array.from(files);
    
    const filePromises = fileArray.map((file) => {
      return new Promise<{ name: string; content: string }>((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const text = e.target?.result as string;
          // Normalize line endings for cross-OS compatibility
          const normalized = text.replace(/\r\n/g, '\n');
          resolve({ name: file.name, content: normalized });
        };
        reader.readAsText(file);
      });
    });

    const results = await Promise.all(filePromises);

    setCode((prevCode) => {
      let newCode = prevCode;
      results.forEach((file) => {
        const separator = newCode.trim() ? "\n\n" : "";
        newCode += `${separator}--- File: ${file.name} ---\n${file.content}`;
      });
      return newCode;
    });

    // Reset input so you can upload from a different directory immediately
    event.target.value = '';
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const selectOptions = models.map(model => ({
    value: model.value,
    label: model.label,
  }));

  return (
    <div className="page-wrapper">
      <header className="top-section">
        <h1 className="logo">🛡️ PR Guardian</h1>
        <div className="select-container" style={{ minWidth: '300px' }}>
          <Select
            isMulti
            instanceId="model-selector"
            value={selectedOptions}
            onChange={(val) => setSelectedOptions(val ? [...val] : [])}
            isOptionDisabled={() => selectedOptions.length >= 3}
            options={selectOptions}
            styles={customStyles}
            placeholder="Select models..."
          />
        </div>
      </header>

      <main className="input-section">
        <div className="input-row">
          <textarea
            className="code-box"
            placeholder="Paste your code here..."
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
          <div className="side-actions">
            <div className="upload-group">
              <label className="field-label">File Upload</label>
              <label className="action-btn" style={{ cursor: 'pointer' }}>
                📁 Upload Files
                <input 
                  type="file" 
                  multiple
                  hidden 
                  onChange={handleFileUpload} 
                  accept=".py,.js,.tsx,.ts,.cs,.txt, jsx, java, go, rb, php, cpp, c, cs, swift, kt, rs" 
                />
              </label>
            </div>
            <div className="upload-group">
              <label className="field-label">Google Drive</label>
              <button className="action-btn">
                <img src="https://upload.wikimedia.org/wikipedia/commons/1/12/Google_Drive_icon_%282020%29.svg" alt="Drive" style={{ width: '18px' }} />
                Google Drive
              </button>
            </div>
          </div>
        </div>

        <div className="submit-row">
          <button className="submit-btn" onClick={handleAudit}>🚀 Start 5-Pillar Audit</button>
        </div>

        <div className="results-grid" style={{ 
          display: 'grid', 
          gridTemplateColumns: `repeat(${selectedOptions.length || 1}, 1fr)`, 
          gap: '20px',
          marginTop: '30px'
        }}>
          {selectedOptions.map(option => (
            <div key={option.value} className="result-column" style={{
              background: '#2c2c2c', // Same as input box
              borderRadius: '8px',
              padding: '15px',
              border: '1px solid #444',
              minHeight: '400px',
              maxHeight: '600px',
              overflowY: 'auto'
            }}>
              <h3 style={{ borderBottom: '2px solid #007bff', paddingBottom: '5px', color: '#ffffff' }}>
                {option.label}
              </h3>
              <pre style={{ whiteSpace: 'pre-wrap', color: '#ffffff', fontSize: '14px' }}>
                {results[option.value] || "Awaiting audit..."}
              </pre>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

export default App;