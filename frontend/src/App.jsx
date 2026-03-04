import { useState, useEffect } from 'react';
import Select from 'react-select';


function App() {
  const [models, setModels] = useState([]);
  const [selectedOptions, setSelectedOptions] = useState([]);
  const [code, setCode] = useState('');

  const fetchModels = async () => {
    try {
      const response = await fetch('https://localhost:8000/models');
      if (!response.ok) throw new Error('Network response was not ok');
      const data = await response.json();

      setModels(data);
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  };

  const customStyles = {
    control: (base) => ({
      ...base,
      backgroundColor: 'white',
      color: 'black',
    }),
    singleValue: (base) => ({
      ...base,
      color: 'black', // The text shown in the box after selection
    }),
    menu: (base) => ({
      ...base,
      backgroundColor: 'white',
    }),
    option: (base, state) => ({
      ...base,
      backgroundColor: state.isFocused ? '#deebff' : 'white',
      color: 'black', // The text inside the dropdown list
    }),
    multiValueLabel: (base) => ({
      ...base,
      color: 'black', // The text of the selected options in multi-select
    }),
    menu: (base) => ({
    ...base,
    backgroundColor: 'white',
    zIndex: 9999,      // Force it to the front
    position: 'absolute' 
    }),
    menuList: (base) => ({
      ...base,
      color: 'black'     // Ensure the text inside the list is black
    }),
  };

  const handleAudit = async () => {
    if (!code || selectedOptions.length === 0) {
      alert('Please select at least one model for auditing.');
      return;
    }
  }

  useEffect(() => {
    fetchModels();
  }, []);

  return (
    <div className="page-wrapper">
      <header className="top-section">
        <h1 className="logo">🛡️ PR Guardian</h1>
        <div className="select-container">
          <Select
            isMulti
            value={selectedOptions}
            onChange={(val) => setSelectedOptions(val || [])}
            isOptionDisabled={() => selectedOptions.length >= 3}
            options={models}
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
              <label>File Upload</label>
              <label className="action-btn">
                📁 Upload File
                <input type="file" hidden />
              </label>
            </div>
            
            <div className="upload-group">
              <label>Google Drive</label>
              <button className="action-btn">
                <img 
                  src="https://upload.wikimedia.org/wikipedia/commons/1/12/Google_Drive_icon_%282020%29.svg" 
                  alt="Google Drive" 
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
