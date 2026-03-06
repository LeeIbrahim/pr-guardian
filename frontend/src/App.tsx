import { useState, useEffect } from 'react';
import Select from 'react-select';
import type { StylesConfig, GroupBase, MultiValue } from 'react-select';

interface FetchResult {
  status: string;
  output: string;
}

interface Model {
  id: string;
  name: string;
}

interface MyOption {
  value: string;
  label: string;
}

function App() {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedOptions, setSelectedOptions] = useState<MyOption[]> ([]);
  const [code, setCode] = useState<string>('');
  const [results, setResults] = useState<FetchResult[]>([]);

  const customStyles: StylesConfig<MyOption, true, GroupBase<MyOption>> = {
    control: (base) => ({
      ...base,
      backgroundColor: 'white',
      color: 'black',
    }),
    singleValue: (base) => ({
      ...base,
      color: 'black',
    }),
    multiValue: (base) => ({
      ...base,
      backgroundColor: '#e0e0e0',
    }),
    multiValueLabel: (base) => ({
      ...base,
      color: 'black',
    }),
    menu: (base) => ({
      ...base,
      backgroundColor: 'white',
      zIndex: 9999,
    }),
    menuList: (base) => ({
      ...base,
      color: 'black',
    }),
    option: (base, state) => ({
      ...base,
      backgroundColor: state.isFocused ? '#deebff' : 'white',
      color: 'black',
      cursor: 'pointer',
    }),
  };

  const fetchModels = async (): Promise<void> => {
    try {
      //TODO: standardize this to pull from env file.
      //Using 127.0.0.1 to match uvicorn host
      const response = await fetch('https://127.0.0.1:8000/models'); 
      if (!response.ok)
        throw new Error('Network response was not ok');
      
      const data :Model[] = await response.json();
      setModels(data); 
    
    } catch (error) {

      if (error instanceof Error) {
        alert('There was an error fetching models. Please try again later.');
        console.error('Error fetching models:', error.message);
      } else {
        alert('An unknown error occurred while fetching models. Please try again later.');
        console.error('Error fetching models:', error);
      }
    }
  };

  const handleAudit = async (): Promise<void> => {
    if (!code || selectedOptions.length === 0) {
      alert('Please select at least one model for auditing and input code.');
      return;
    }
    
    // TODO: standardize this to pull from env file.
    const response: Response = await fetch('https://127.0.0.1:8000/review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        "code": code,
        "model_names": selectedOptions.map(opt => opt.value),
      }),
    });

    if (!response.body) {
      alert('There was an error fetching models. Please try again later.');
      console.error('Error fetching models:', response.statusText);
      return;
    }
    console.log("Audit requested for code length:", code.length);
    
    const reader: ReadableStreamDefaultReader<Uint8Array> = response.body.getReader();
    const decoder: TextDecoder = new TextDecoder('utf-8');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk: string= decoder.decode(value, { stream: true });
      const lines: string[]= chunk.split('\n').filter(line => line.trim() !== '');

      lines.forEach(line => {
        if (line.startsWith('data: ')) {
          try {
            const data: FetchResult = JSON.parse(line.replace('data: ', ''));
            setResults(prev => [...prev, data]);
          } catch (err) {
            if (err instanceof Error) {
              console.error('Error parsing model review:', err.message);
            } else {
              console.error('Error parsing model review:', err);
            }
          }
        }
      });
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const selectOptions = models.map(model => ({
    value: model.name,
    label: model.name,
  }));

  return (
    <div className="page-wrapper">
      <header className="top-section">
        <h1 className="logo">🛡️ PR Guardian</h1>
        <div className="select-container">
          <Select
            isMulti
            value={selectedOptions}
            onChange={(val: MultiValue<MyOption>) => setSelectedOptions(val ? [...val] : [])}
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
              <label className="action-btn">
                📁 Upload File
                <input type="file" hidden />
              </label>
            </div>
            
            <div className="upload-group">
              <label className="field-label">Google Drive</label>
              <button className="action-btn">
                <img 
                  src="https://upload.wikimedia.org/wikipedia/commons/1/12/Google_Drive_icon_%282020%29.svg" 
                  alt="Drive" 
                  style={{ width: '18px', height: '18px' }} 
                />
                Google Drive
              </button>
            </div>
          </div>
        </div>

        <div className="submit-row">
          <button className="submit-btn" onClick={handleAudit}>
            🚀 Start 5-Pillar Audit
          </button>
        </div>
      </main>
    </div>
  );
}

export default App;