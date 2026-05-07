import React from 'react';
import { LanguageProvider } from './context/LanguageContext';
import LanguageSwitcher from './components/LanguageSwitcher';
// Your other imports remain the same

function App() {
  return (
    <LanguageProvider>
      <div className="App">
        <nav>
          {/* Add this to your navbar */}
          <LanguageSwitcher />
          {/* Rest of your navigation */}
        </nav>
        
        {/* Your existing routes/components */}
      </div>
    </LanguageProvider>
  );
}

export default App;
